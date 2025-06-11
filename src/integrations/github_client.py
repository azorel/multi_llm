import asyncio
import json
import uuid
import hashlib
import time
import base64
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import aiohttp
import git
import sqlite3
from pathlib import Path
from loguru import logger
import threading
import subprocess
import tempfile
import shutil
import yaml
import difflib


class PullRequestState(Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class IssueState(Enum):
    OPEN = "open"
    CLOSED = "closed"


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    CANCELLED = "cancelled"


class ReleaseType(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    PRERELEASE = "prerelease"


@dataclass
class GitHubRepository:
    owner: str
    name: str
    full_name: str
    description: Optional[str]
    default_branch: str
    private: bool
    clone_url: str
    ssh_url: str
    html_url: str
    created_at: datetime
    updated_at: datetime
    language: Optional[str] = None
    topics: List[str] = field(default_factory=list)


@dataclass
class GitHubBranch:
    name: str
    sha: str
    protected: bool
    repository: str
    created_at: datetime
    author: str
    commit_message: str


@dataclass
class GitHubCommit:
    sha: str
    message: str
    author: str
    author_email: str
    committer: str
    committer_email: str
    timestamp: datetime
    branch: str
    files_changed: List[Dict[str, Any]]
    additions: int
    deletions: int
    repository: str


@dataclass
class GitHubPullRequest:
    pr_id: int
    number: int
    title: str
    description: str
    state: PullRequestState
    author: str
    head_branch: str
    base_branch: str
    repository: str
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None
    mergeable: Optional[bool] = None
    draft: bool = False
    commits: int = 0
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    reviewers: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    checks_status: Optional[str] = None


@dataclass
class GitHubIssue:
    issue_id: int
    number: int
    title: str
    description: str
    state: IssueState
    author: str
    assignees: List[str]
    labels: List[str]
    milestone: Optional[str]
    repository: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    comments: int = 0


@dataclass
class TestResults:
    test_run_id: str
    repository: str
    branch: str
    commit_sha: str
    status: TestStatus
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    execution_time: float
    coverage_percentage: Optional[float]
    test_output: str
    failed_test_details: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class ReleaseInfo:
    release_id: str
    tag_name: str
    release_name: str
    description: str
    draft: bool
    prerelease: bool
    target_commitish: str
    repository: str
    created_at: datetime
    published_at: Optional[datetime] = None
    assets: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CodeReviewRequest:
    request_id: str
    pull_request: int
    reviewers: List[str]
    review_type: str  # "required", "optional", "automated"
    deadline: Optional[datetime]
    context: Dict[str, Any]
    created_at: datetime
    status: str = "pending"


class GitHubAPIClient:
    """Low-level GitHub API client."""
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset_time = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper headers."""
        if self.session is None or self.session.closed:
            headers = {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Autonomous-Multi-LLM-Agent/1.0'
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        
        return self.session
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to GitHub API with rate limit handling."""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Check rate limits
        if self.rate_limit_remaining <= 10:
            if self.rate_limit_reset_time and datetime.now() < self.rate_limit_reset_time:
                wait_time = (self.rate_limit_reset_time - datetime.now()).total_seconds()
                logger.warning(f"Rate limit reached, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
        
        async with session.request(method, url, json=data, params=params) as response:
            # Update rate limit info
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            reset_timestamp = response.headers.get('X-RateLimit-Reset')
            if reset_timestamp:
                self.rate_limit_reset_time = datetime.fromtimestamp(int(reset_timestamp))
            
            response_data = await response.json()
            
            if response.status >= 400:
                error_msg = response_data.get('message', f'HTTP {response.status}')
                logger.error(f"GitHub API error: {error_msg}")
                raise Exception(f"GitHub API error: {error_msg}")
            
            return response_data
    
    async def close(self):
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()


class GitOperations:
    """Git operations for local repository management."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo: Optional[git.Repo] = None
        self._ensure_repo()
    
    def _ensure_repo(self):
        """Ensure we have a valid git repository."""
        try:
            if self.repo_path.exists():
                self.repo = git.Repo(self.repo_path)
            else:
                logger.error(f"Repository path does not exist: {self.repo_path}")
        except git.exc.InvalidGitRepositoryError:
            logger.error(f"Invalid git repository: {self.repo_path}")
    
    def create_branch(self, branch_name: str, base_branch: str = "main") -> bool:
        """Create a new branch."""
        if not self.repo:
            return False
        
        try:
            # Checkout base branch
            self.repo.git.checkout(base_branch)
            
            # Create and checkout new branch
            self.repo.git.checkout('-b', branch_name)
            
            logger.info(f"Created branch: {branch_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False
    
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a branch."""
        if not self.repo:
            return False
        
        try:
            self.repo.git.checkout(branch_name)
            logger.info(f"Switched to branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to branch {branch_name}: {e}")
            return False
    
    def add_files(self, file_paths: List[str]) -> bool:
        """Add files to staging area."""
        if not self.repo:
            return False
        
        try:
            for file_path in file_paths:
                self.repo.git.add(file_path)
            
            logger.debug(f"Added {len(file_paths)} files to staging")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add files: {e}")
            return False
    
    def commit_changes(self, message: str, author_name: str = "Autonomous Agent", 
                      author_email: str = "agent@autonomous.ai") -> Optional[str]:
        """Commit staged changes."""
        if not self.repo:
            return None
        
        try:
            # Check if there are changes to commit
            if not self.repo.is_dirty(index=True):
                logger.warning("No changes to commit")
                return None
            
            # Set author info
            with self.repo.config_writer() as config:
                config.set_value("user", "name", author_name)
                config.set_value("user", "email", author_email)
            
            # Commit changes
            commit = self.repo.index.commit(message)
            
            logger.info(f"Committed changes: {commit.hexsha[:8]} - {message}")
            return commit.hexsha
            
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            return None
    
    def push_branch(self, branch_name: str, remote: str = "origin") -> bool:
        """Push branch to remote."""
        if not self.repo:
            return False
        
        try:
            origin = self.repo.remote(remote)
            origin.push(branch_name)
            
            logger.info(f"Pushed branch {branch_name} to {remote}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to push branch {branch_name}: {e}")
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """Get current branch name."""
        if not self.repo:
            return None
        
        try:
            return self.repo.active_branch.name
        except Exception:
            return None
    
    def get_modified_files(self) -> List[str]:
        """Get list of modified files."""
        if not self.repo:
            return []
        
        try:
            # Get both staged and unstaged changes
            staged_files = [item.a_path for item in self.repo.index.diff("HEAD")]
            unstaged_files = [item.a_path for item in self.repo.index.diff(None)]
            
            return list(set(staged_files + unstaged_files))
            
        except Exception as e:
            logger.error(f"Failed to get modified files: {e}")
            return []
    
    def get_file_diff(self, file_path: str) -> str:
        """Get diff for a specific file."""
        if not self.repo:
            return ""
        
        try:
            return self.repo.git.diff(file_path)
        except Exception as e:
            logger.error(f"Failed to get diff for {file_path}: {e}")
            return ""


class GitHubIntegration:
    """Comprehensive GitHub integration for autonomous multi-LLM agents."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # GitHub API configuration
        self.github_token = config.get('github_token')
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        self.api_client = GitHubAPIClient(self.github_token)
        
        # Repository configuration
        self.default_owner = config.get('default_owner')
        self.default_repo = config.get('default_repo')
        self.local_repo_path = config.get('local_repo_path', './repo')
        
        # Git operations
        self.git_ops = GitOperations(self.local_repo_path)
        
        # Local database for tracking
        self.db_path = config.get('github_db_path', 'github_integration.db')
        self._initialize_database()
        
        # Automation settings
        self.auto_commit_enabled = config.get('auto_commit_enabled', True)
        self.auto_test_enabled = config.get('auto_test_enabled', True)
        self.auto_pr_enabled = config.get('auto_pr_enabled', False)
        self.auto_review_enabled = config.get('auto_review_enabled', True)
        
        # Workflow templates
        self.workflow_templates = config.get('workflow_templates', {})
        
        # Data storage
        self.repositories: Dict[str, GitHubRepository] = {}
        self.pull_requests: Dict[int, GitHubPullRequest] = {}
        self.issues: Dict[int, GitHubIssue] = {}
        self.test_runs: Dict[str, TestResults] = {}
        
        # Threading
        self.operation_lock = threading.RLock()
        
        logger.info(f"GitHubIntegration initialized for {self.default_owner}/{self.default_repo}")
    
    def _initialize_database(self):
        """Initialize SQLite database for tracking GitHub operations."""
        conn = sqlite3.connect(self.db_path)
        
        # Repositories table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS repositories (
                full_name TEXT PRIMARY KEY,
                owner TEXT,
                name TEXT,
                description TEXT,
                default_branch TEXT,
                private INTEGER,
                clone_url TEXT,
                ssh_url TEXT,
                html_url TEXT,
                created_at TEXT,
                updated_at TEXT,
                language TEXT,
                topics TEXT
            )
        ''')
        
        # Pull requests table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pull_requests (
                pr_id INTEGER PRIMARY KEY,
                number INTEGER,
                title TEXT,
                description TEXT,
                state TEXT,
                author TEXT,
                head_branch TEXT,
                base_branch TEXT,
                repository TEXT,
                created_at TEXT,
                updated_at TEXT,
                merged_at TEXT,
                mergeable INTEGER,
                draft INTEGER,
                commits INTEGER,
                additions INTEGER,
                deletions INTEGER,
                changed_files INTEGER,
                reviewers TEXT,
                labels TEXT,
                checks_status TEXT
            )
        ''')
        
        # Issues table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                issue_id INTEGER PRIMARY KEY,
                number INTEGER,
                title TEXT,
                description TEXT,
                state TEXT,
                author TEXT,
                assignees TEXT,
                labels TEXT,
                milestone TEXT,
                repository TEXT,
                created_at TEXT,
                updated_at TEXT,
                closed_at TEXT,
                comments INTEGER
            )
        ''')
        
        # Test runs table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                test_run_id TEXT PRIMARY KEY,
                repository TEXT,
                branch TEXT,
                commit_sha TEXT,
                status TEXT,
                total_tests INTEGER,
                passed_tests INTEGER,
                failed_tests INTEGER,
                skipped_tests INTEGER,
                execution_time REAL,
                coverage_percentage REAL,
                test_output TEXT,
                failed_test_details TEXT,
                started_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # Commits table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS commits (
                sha TEXT PRIMARY KEY,
                message TEXT,
                author TEXT,
                author_email TEXT,
                committer TEXT,
                committer_email TEXT,
                timestamp TEXT,
                branch TEXT,
                files_changed TEXT,
                additions INTEGER,
                deletions INTEGER,
                repository TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # Core version control methods
    
    async def commit_code(self, files: List[Dict[str, Any]], message: str,
                         branch: Optional[str] = None) -> Optional[str]:
        """Commit code changes to repository."""
        try:
            with self.operation_lock:
                # Switch to target branch if specified
                if branch and branch != self.git_ops.get_current_branch():
                    if not self.git_ops.switch_branch(branch):
                        logger.error(f"Failed to switch to branch: {branch}")
                        return None
                
                # Write files to disk
                for file_info in files:
                    file_path = Path(self.local_repo_path) / file_info['path']
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_info['content'])
                
                # Add files to git
                file_paths = [file_info['path'] for file_info in files]
                if not self.git_ops.add_files(file_paths):
                    logger.error("Failed to add files to git")
                    return None
                
                # Commit changes
                commit_sha = self.git_ops.commit_changes(message)
                if not commit_sha:
                    logger.error("Failed to commit changes")
                    return None
                
                # Push to remote if auto-commit enabled
                if self.auto_commit_enabled:
                    current_branch = self.git_ops.get_current_branch()
                    if current_branch:
                        self.git_ops.push_branch(current_branch)
                
                # Store commit info
                await self._store_commit_info(commit_sha, message, files, branch or "main")
                
                logger.info(f"Successfully committed code: {commit_sha[:8]}")
                return commit_sha
                
        except Exception as e:
            logger.error(f"Failed to commit code: {e}")
            return None
    
    async def create_branch(self, name: str, base_branch: str = "main") -> bool:
        """Create a new branch."""
        try:
            with self.operation_lock:
                # Create branch locally
                if not self.git_ops.create_branch(name, base_branch):
                    return False
                
                # Push to remote
                if self.auto_commit_enabled:
                    self.git_ops.push_branch(name)
                
                # Store branch info in database
                await self._store_branch_info(name, base_branch)
                
                logger.info(f"Created branch: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create branch {name}: {e}")
            return False
    
    async def create_pull_request(self, title: str, description: str,
                                head_branch: str, base_branch: str = "main",
                                draft: bool = False, reviewers: List[str] = None) -> Optional[int]:
        """Create a pull request."""
        try:
            # Prepare PR data
            pr_data = {
                "title": title,
                "body": description,
                "head": head_branch,
                "base": base_branch,
                "draft": draft
            }
            
            # Create PR via API
            response = await self.api_client._make_request(
                "POST",
                f"repos/{self.default_owner}/{self.default_repo}/pulls",
                pr_data
            )
            
            pr_number = response.get('number')
            pr_id = response.get('id')
            
            # Add reviewers if specified
            if reviewers:
                await self.request_code_review(pr_number, reviewers)
            
            # Store PR info
            pr = GitHubPullRequest(
                pr_id=pr_id,
                number=pr_number,
                title=title,
                description=description,
                state=PullRequestState.OPEN,
                author=response.get('user', {}).get('login', 'unknown'),
                head_branch=head_branch,
                base_branch=base_branch,
                repository=f"{self.default_owner}/{self.default_repo}",
                created_at=datetime.fromisoformat(response.get('created_at', '').replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(response.get('updated_at', '').replace('Z', '+00:00')),
                draft=draft,
                reviewers=reviewers or []
            )
            
            self.pull_requests[pr_number] = pr
            await self._store_pull_request(pr)
            
            logger.info(f"Created pull request #{pr_number}: {title}")
            return pr_number
            
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return None
    
    async def run_tests(self, branch: Optional[str] = None,
                       test_command: Optional[str] = None) -> TestResults:
        """Run tests on the current or specified branch."""
        test_run_id = str(uuid.uuid4())
        current_branch = branch or self.git_ops.get_current_branch() or "main"
        
        # Get current commit SHA
        commit_sha = self.git_ops.repo.head.commit.hexsha if self.git_ops.repo else "unknown"
        
        # Initialize test results
        test_results = TestResults(
            test_run_id=test_run_id,
            repository=f"{self.default_owner}/{self.default_repo}",
            branch=current_branch,
            commit_sha=commit_sha,
            status=TestStatus.RUNNING,
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            execution_time=0.0,
            coverage_percentage=None,
            test_output=""
        )
        
        try:
            # Determine test command
            if not test_command:
                test_command = self._detect_test_command()
            
            if not test_command:
                test_results.status = TestStatus.ERROR
                test_results.test_output = "No test command detected"
                return test_results
            
            # Run tests
            start_time = time.time()
            
            process = await asyncio.create_subprocess_shell(
                test_command,
                cwd=self.local_repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            stdout, _ = await process.communicate()
            
            test_results.execution_time = time.time() - start_time
            test_results.test_output = stdout.decode('utf-8') if stdout else ""
            test_results.completed_at = datetime.now()
            
            # Parse test results
            await self._parse_test_output(test_results)
            
            # Determine overall status
            if process.returncode == 0:
                test_results.status = TestStatus.SUCCESS
            else:
                test_results.status = TestStatus.FAILURE
            
            # Store test results
            self.test_runs[test_run_id] = test_results
            await self._store_test_results(test_results)
            
            logger.info(f"Test run completed: {test_results.status.value}")
            return test_results
            
        except Exception as e:
            test_results.status = TestStatus.ERROR
            test_results.test_output = f"Test execution failed: {str(e)}"
            test_results.completed_at = datetime.now()
            
            logger.error(f"Test execution failed: {e}")
            return test_results
    
    async def merge_changes(self, pr_number: int, merge_method: str = "merge") -> bool:
        """Merge a pull request."""
        try:
            # Check if PR exists and is mergeable
            if pr_number not in self.pull_requests:
                # Fetch PR info
                await self._fetch_pull_request_info(pr_number)
            
            if pr_number not in self.pull_requests:
                logger.error(f"Pull request #{pr_number} not found")
                return False
            
            pr = self.pull_requests[pr_number]
            
            # Merge via API
            merge_data = {
                "commit_title": f"Merge pull request #{pr_number}",
                "commit_message": pr.title,
                "merge_method": merge_method
            }
            
            response = await self.api_client._make_request(
                "PUT",
                f"repos/{self.default_owner}/{self.default_repo}/pulls/{pr_number}/merge",
                merge_data
            )
            
            if response.get('merged'):
                # Update PR status
                pr.state = PullRequestState.MERGED
                pr.merged_at = datetime.now()
                await self._store_pull_request(pr)
                
                logger.info(f"Successfully merged PR #{pr_number}")
                return True
            else:
                logger.error(f"Failed to merge PR #{pr_number}: {response.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to merge PR #{pr_number}: {e}")
            return False
    
    # Collaboration features
    
    async def create_issue(self, title: str, description: str,
                          labels: List[str] = None, assignees: List[str] = None,
                          milestone: Optional[str] = None) -> Optional[int]:
        """Create a GitHub issue."""
        try:
            issue_data = {
                "title": title,
                "body": description
            }
            
            if labels:
                issue_data["labels"] = labels
            
            if assignees:
                issue_data["assignees"] = assignees
            
            if milestone:
                issue_data["milestone"] = milestone
            
            response = await self.api_client._make_request(
                "POST",
                f"repos/{self.default_owner}/{self.default_repo}/issues",
                issue_data
            )
            
            issue_number = response.get('number')
            issue_id = response.get('id')
            
            # Store issue info
            issue = GitHubIssue(
                issue_id=issue_id,
                number=issue_number,
                title=title,
                description=description,
                state=IssueState.OPEN,
                author=response.get('user', {}).get('login', 'unknown'),
                assignees=assignees or [],
                labels=labels or [],
                milestone=milestone,
                repository=f"{self.default_owner}/{self.default_repo}",
                created_at=datetime.fromisoformat(response.get('created_at', '').replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(response.get('updated_at', '').replace('Z', '+00:00'))
            )
            
            self.issues[issue_number] = issue
            await self._store_issue(issue)
            
            logger.info(f"Created issue #{issue_number}: {title}")
            return issue_number
            
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None
    
    async def request_code_review(self, pr_number: int, reviewers: List[str],
                                 review_type: str = "required") -> bool:
        """Request code review for a pull request."""
        try:
            review_data = {
                "reviewers": reviewers
            }
            
            await self.api_client._make_request(
                "POST",
                f"repos/{self.default_owner}/{self.default_repo}/pulls/{pr_number}/requested_reviewers",
                review_data
            )
            
            # Store review request
            request = CodeReviewRequest(
                request_id=str(uuid.uuid4()),
                pull_request=pr_number,
                reviewers=reviewers,
                review_type=review_type,
                deadline=datetime.now() + timedelta(days=3),  # Default 3-day deadline
                context={"automated_request": True},
                created_at=datetime.now()
            )
            
            logger.info(f"Requested code review for PR #{pr_number} from {reviewers}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to request code review: {e}")
            return False
    
    async def update_documentation(self, files: List[Dict[str, Any]], 
                                 commit_message: str = "Update documentation") -> bool:
        """Update documentation files."""
        try:
            # Create documentation branch
            doc_branch = f"docs/auto-update-{int(time.time())}"
            if not await self.create_branch(doc_branch):
                return False
            
            # Commit documentation changes
            commit_sha = await self.commit_code(files, commit_message, doc_branch)
            if not commit_sha:
                return False
            
            # Create PR for documentation update
            pr_number = await self.create_pull_request(
                title="📚 Automated Documentation Update",
                description=f"Automatic documentation update\n\nCommit: {commit_sha}\n\nFiles updated:\n" + 
                           "\n".join([f"- {f['path']}" for f in files]),
                head_branch=doc_branch,
                base_branch="main",
                labels=["documentation", "automated"]
            )
            
            if pr_number and self.auto_pr_enabled:
                # Auto-merge documentation PRs if tests pass
                test_results = await self.run_tests(doc_branch)
                if test_results.status == TestStatus.SUCCESS:
                    await self.merge_changes(pr_number)
            
            logger.info(f"Updated documentation in PR #{pr_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update documentation: {e}")
            return False
    
    async def create_release(self, version: str, release_type: ReleaseType,
                           changelog: Optional[str] = None,
                           prerelease: bool = False) -> Optional[str]:
        """Create a new release."""
        try:
            # Generate changelog if not provided
            if not changelog:
                changelog = await self._generate_changelog(version)
            
            release_data = {
                "tag_name": version,
                "target_commitish": "main",
                "name": f"Release {version}",
                "body": changelog,
                "draft": False,
                "prerelease": prerelease
            }
            
            response = await self.api_client._make_request(
                "POST",
                f"repos/{self.default_owner}/{self.default_repo}/releases",
                release_data
            )
            
            release_id = response.get('id')
            
            # Store release info
            release = ReleaseInfo(
                release_id=str(release_id),
                tag_name=version,
                release_name=f"Release {version}",
                description=changelog,
                draft=False,
                prerelease=prerelease,
                target_commitish="main",
                repository=f"{self.default_owner}/{self.default_repo}",
                created_at=datetime.fromisoformat(response.get('created_at', '').replace('Z', '+00:00')),
                published_at=datetime.fromisoformat(response.get('published_at', '').replace('Z', '+00:00'))
            )
            
            logger.info(f"Created release: {version}")
            return str(release_id)
            
        except Exception as e:
            logger.error(f"Failed to create release: {e}")
            return None
    
    async def send_team_notification(self, message: str, channels: List[str] = None) -> bool:
        """Send team notification about repository events."""
        try:
            # Create notification issue
            notification_title = f"🔔 Team Notification - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            issue_number = await self.create_issue(
                title=notification_title,
                description=message,
                labels=["notification", "automated"]
            )
            
            logger.info(f"Created team notification issue #{issue_number}")
            return issue_number is not None
            
        except Exception as e:
            logger.error(f"Failed to send team notification: {e}")
            return False
    
    # Automation features
    
    async def auto_commit_generated_code(self, code_files: List[Dict[str, Any]],
                                       context: Dict[str, Any]) -> Optional[str]:
        """Automatically commit generated code with proper context."""
        try:
            # Generate commit message
            commit_message = self._generate_commit_message(code_files, context)
            
            # Create feature branch
            branch_name = f"feature/auto-generated-{int(time.time())}"
            if not await self.create_branch(branch_name):
                return None
            
            # Commit code
            commit_sha = await self.commit_code(code_files, commit_message, branch_name)
            if not commit_sha:
                return None
            
            # Run tests if enabled
            if self.auto_test_enabled:
                test_results = await self.run_tests(branch_name)
                
                if test_results.status == TestStatus.FAILURE:
                    # Create issue for test failures
                    await self.create_issue_for_failure(
                        "Test Failures in Auto-Generated Code",
                        f"Tests failed for auto-generated code in branch {branch_name}\n\n" +
                        f"Commit: {commit_sha}\n\n" +
                        f"Test output:\n```\n{test_results.test_output}\n```",
                        ["bug", "automated", "test-failure"]
                    )
                    return commit_sha
            
            # Create PR if enabled
            if self.auto_pr_enabled:
                pr_number = await self.create_pull_request(
                    title=f"🤖 Auto-generated code: {context.get('task_name', 'Code Generation')}",
                    description=self._generate_pr_description(code_files, context, commit_sha),
                    head_branch=branch_name,
                    base_branch="main",
                    labels=["automated", "code-generation"]
                )
                
                # Request review if enabled
                if self.auto_review_enabled and pr_number:
                    reviewers = context.get('reviewers', [])
                    if reviewers:
                        await self.request_code_review(pr_number, reviewers)
            
            logger.info(f"Auto-committed generated code: {commit_sha}")
            return commit_sha
            
        except Exception as e:
            logger.error(f"Failed to auto-commit generated code: {e}")
            return None
    
    async def setup_ci_cd_workflow(self, workflow_config: Dict[str, Any]) -> bool:
        """Set up CI/CD workflow."""
        try:
            workflow_name = workflow_config.get('name', 'ci-cd')
            
            # Generate GitHub Actions workflow
            workflow_content = self._generate_workflow_yaml(workflow_config)
            
            # Create workflow file
            workflow_file = {
                'path': f'.github/workflows/{workflow_name}.yml',
                'content': workflow_content
            }
            
            # Commit workflow
            commit_sha = await self.commit_code(
                [workflow_file],
                f"Add {workflow_name} CI/CD workflow",
                "main"
            )
            
            if commit_sha:
                logger.info(f"Set up CI/CD workflow: {workflow_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to setup CI/CD workflow: {e}")
            return False
    
    async def generate_and_update_changelog(self, version: str) -> bool:
        """Generate and update changelog."""
        try:
            changelog = await self._generate_changelog(version)
            
            # Update CHANGELOG.md
            changelog_file = {
                'path': 'CHANGELOG.md',
                'content': changelog
            }
            
            commit_sha = await self.commit_code(
                [changelog_file],
                f"Update changelog for {version}",
                "main"
            )
            
            if commit_sha:
                logger.info(f"Updated changelog for version {version}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update changelog: {e}")
            return False
    
    async def create_issue_for_failure(self, title: str, description: str,
                                     labels: List[str] = None) -> Optional[int]:
        """Create an issue for tracking failures."""
        failure_labels = ["bug", "automated"] + (labels or [])
        
        # Add failure analysis to description
        enhanced_description = f"{description}\n\n## Failure Analysis\n\n"
        enhanced_description += f"- **Timestamp**: {datetime.now().isoformat()}\n"
        enhanced_description += f"- **Repository**: {self.default_owner}/{self.default_repo}\n"
        enhanced_description += f"- **Branch**: {self.git_ops.get_current_branch()}\n"
        
        return await self.create_issue(
            title=title,
            description=enhanced_description,
            labels=failure_labels
        )
    
    # Helper methods
    
    def _detect_test_command(self) -> Optional[str]:
        """Detect appropriate test command based on project type."""
        repo_path = Path(self.local_repo_path)
        
        # Python projects
        if (repo_path / "pytest.ini").exists() or (repo_path / "setup.cfg").exists():
            return "python -m pytest --tb=short -v"
        elif (repo_path / "requirements.txt").exists():
            return "python -m unittest discover -v"
        
        # Node.js projects
        elif (repo_path / "package.json").exists():
            return "npm test"
        
        # Go projects
        elif (repo_path / "go.mod").exists():
            return "go test ./..."
        
        # Rust projects
        elif (repo_path / "Cargo.toml").exists():
            return "cargo test"
        
        # Java projects
        elif (repo_path / "pom.xml").exists():
            return "mvn test"
        elif (repo_path / "build.gradle").exists():
            return "gradle test"
        
        return None
    
    async def _parse_test_output(self, test_results: TestResults):
        """Parse test output to extract statistics."""
        output = test_results.test_output.lower()
        
        # Pytest output parsing
        if "pytest" in output:
            # Look for patterns like "3 passed, 1 failed"
            import re
            passed_match = re.search(r'(\d+)\s+passed', output)
            failed_match = re.search(r'(\d+)\s+failed', output)
            skipped_match = re.search(r'(\d+)\s+skipped', output)
            
            if passed_match:
                test_results.passed_tests = int(passed_match.group(1))
            if failed_match:
                test_results.failed_tests = int(failed_match.group(1))
            if skipped_match:
                test_results.skipped_tests = int(skipped_match.group(1))
            
            test_results.total_tests = test_results.passed_tests + test_results.failed_tests + test_results.skipped_tests
        
        # Coverage parsing
        coverage_match = re.search(r'total.*?(\d+)%', output)
        if coverage_match:
            test_results.coverage_percentage = float(coverage_match.group(1))
    
    def _generate_commit_message(self, files: List[Dict[str, Any]], 
                                context: Dict[str, Any]) -> str:
        """Generate descriptive commit message."""
        task_name = context.get('task_name', 'Code generation')
        file_count = len(files)
        
        # Determine commit type
        if any('test' in f['path'].lower() for f in files):
            commit_type = "test"
        elif any('doc' in f['path'].lower() or 'readme' in f['path'].lower() for f in files):
            commit_type = "docs"
        elif any(f['path'].endswith('.py') or f['path'].endswith('.js') for f in files):
            commit_type = "feat"
        else:
            commit_type = "chore"
        
        message = f"{commit_type}: {task_name}"
        
        if file_count > 1:
            message += f" ({file_count} files)"
        
        # Add context if available
        if context.get('agent_id'):
            message += f"\n\nGenerated by: {context['agent_id']}"
        
        if context.get('execution_id'):
            message += f"\nExecution ID: {context['execution_id']}"
        
        return message
    
    def _generate_pr_description(self, files: List[Dict[str, Any]], 
                                context: Dict[str, Any], commit_sha: str) -> str:
        """Generate PR description."""
        description = f"## 🤖 Automated Code Generation\n\n"
        description += f"**Task**: {context.get('task_name', 'Code Generation')}\n"
        description += f"**Agent**: {context.get('agent_id', 'Unknown')}\n"
        description += f"**Commit**: {commit_sha}\n\n"
        
        description += "### Files Modified\n\n"
        for file_info in files:
            description += f"- `{file_info['path']}`\n"
        
        if context.get('execution_results'):
            description += f"\n### Execution Results\n\n"
            description += f"```json\n{json.dumps(context['execution_results'], indent=2)}\n```\n"
        
        description += "\n### Review Checklist\n\n"
        description += "- [ ] Code follows project standards\n"
        description += "- [ ] Tests are included and pass\n"
        description += "- [ ] Documentation is updated\n"
        description += "- [ ] No security vulnerabilities\n"
        
        return description
    
    def _generate_workflow_yaml(self, config: Dict[str, Any]) -> str:
        """Generate GitHub Actions workflow YAML."""
        workflow = {
            'name': config.get('name', 'CI/CD'),
            'on': {
                'push': {
                    'branches': config.get('trigger_branches', ['main', 'develop'])
                },
                'pull_request': {
                    'branches': ['main']
                }
            },
            'jobs': {
                'test': {
                    'runs-on': 'ubuntu-latest',
                    'steps': [
                        {
                            'uses': 'actions/checkout@v3'
                        },
                        {
                            'name': 'Set up environment',
                            'uses': 'actions/setup-python@v4',
                            'with': {
                                'python-version': config.get('python_version', '3.9')
                            }
                        },
                        {
                            'name': 'Install dependencies',
                            'run': config.get('install_command', 'pip install -r requirements.txt')
                        },
                        {
                            'name': 'Run tests',
                            'run': config.get('test_command', 'python -m pytest')
                        }
                    ]
                }
            }
        }
        
        return yaml.dump(workflow, default_flow_style=False)
    
    async def _generate_changelog(self, version: str) -> str:
        """Generate changelog content."""
        changelog = f"# Changelog\n\n"
        changelog += f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Get recent commits
        if self.git_ops.repo:
            commits = list(self.git_ops.repo.iter_commits(max_count=20))
            
            features = []
            fixes = []
            others = []
            
            for commit in commits:
                message = commit.message.strip()
                if message.startswith('feat:'):
                    features.append(message)
                elif message.startswith('fix:'):
                    fixes.append(message)
                else:
                    others.append(message)
            
            if features:
                changelog += "### ✨ Features\n\n"
                for feature in features:
                    changelog += f"- {feature[5:].strip()}\n"
                changelog += "\n"
            
            if fixes:
                changelog += "### 🐛 Bug Fixes\n\n"
                for fix in fixes:
                    changelog += f"- {fix[4:].strip()}\n"
                changelog += "\n"
            
            if others:
                changelog += "### 🔧 Other Changes\n\n"
                for change in others[:10]:  # Limit to 10 other changes
                    changelog += f"- {change}\n"
        
        return changelog
    
    # Database storage methods
    
    async def _store_commit_info(self, commit_sha: str, message: str, 
                                files: List[Dict[str, Any]], branch: str):
        """Store commit information in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO commits
                (sha, message, author, author_email, committer, committer_email,
                 timestamp, branch, files_changed, additions, deletions, repository)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                commit_sha,
                message,
                "Autonomous Agent",
                "agent@autonomous.ai",
                "Autonomous Agent",
                "agent@autonomous.ai",
                datetime.now().isoformat(),
                branch,
                json.dumps([f['path'] for f in files]),
                sum(len(f['content'].split('\n')) for f in files),
                0,  # Deletions not tracked for new files
                f"{self.default_owner}/{self.default_repo}"
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store commit info: {e}")
    
    async def _store_branch_info(self, branch_name: str, base_branch: str):
        """Store branch information."""
        # Branch info is tracked through git operations
        pass
    
    async def _store_pull_request(self, pr: GitHubPullRequest):
        """Store pull request in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO pull_requests
                (pr_id, number, title, description, state, author, head_branch, base_branch,
                 repository, created_at, updated_at, merged_at, mergeable, draft, commits,
                 additions, deletions, changed_files, reviewers, labels, checks_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pr.pr_id,
                pr.number,
                pr.title,
                pr.description,
                pr.state.value,
                pr.author,
                pr.head_branch,
                pr.base_branch,
                pr.repository,
                pr.created_at.isoformat(),
                pr.updated_at.isoformat(),
                pr.merged_at.isoformat() if pr.merged_at else None,
                1 if pr.mergeable else 0,
                1 if pr.draft else 0,
                pr.commits,
                pr.additions,
                pr.deletions,
                pr.changed_files,
                json.dumps(pr.reviewers),
                json.dumps(pr.labels),
                pr.checks_status
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store pull request: {e}")
    
    async def _store_issue(self, issue: GitHubIssue):
        """Store issue in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO issues
                (issue_id, number, title, description, state, author, assignees,
                 labels, milestone, repository, created_at, updated_at, closed_at, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                issue.issue_id,
                issue.number,
                issue.title,
                issue.description,
                issue.state.value,
                issue.author,
                json.dumps(issue.assignees),
                json.dumps(issue.labels),
                issue.milestone,
                issue.repository,
                issue.created_at.isoformat(),
                issue.updated_at.isoformat(),
                issue.closed_at.isoformat() if issue.closed_at else None,
                issue.comments
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store issue: {e}")
    
    async def _store_test_results(self, test_results: TestResults):
        """Store test results in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO test_runs
                (test_run_id, repository, branch, commit_sha, status, total_tests,
                 passed_tests, failed_tests, skipped_tests, execution_time,
                 coverage_percentage, test_output, failed_test_details,
                 started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_results.test_run_id,
                test_results.repository,
                test_results.branch,
                test_results.commit_sha,
                test_results.status.value,
                test_results.total_tests,
                test_results.passed_tests,
                test_results.failed_tests,
                test_results.skipped_tests,
                test_results.execution_time,
                test_results.coverage_percentage,
                test_results.test_output,
                json.dumps(test_results.failed_test_details),
                test_results.started_at.isoformat(),
                test_results.completed_at.isoformat() if test_results.completed_at else None
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to store test results: {e}")
    
    async def _fetch_pull_request_info(self, pr_number: int):
        """Fetch pull request information from GitHub API."""
        try:
            response = await self.api_client._make_request(
                "GET",
                f"repos/{self.default_owner}/{self.default_repo}/pulls/{pr_number}"
            )
            
            # Convert to GitHubPullRequest object
            pr = GitHubPullRequest(
                pr_id=response.get('id'),
                number=response.get('number'),
                title=response.get('title'),
                description=response.get('body', ''),
                state=PullRequestState(response.get('state')),
                author=response.get('user', {}).get('login', 'unknown'),
                head_branch=response.get('head', {}).get('ref', ''),
                base_branch=response.get('base', {}).get('ref', ''),
                repository=f"{self.default_owner}/{self.default_repo}",
                created_at=datetime.fromisoformat(response.get('created_at', '').replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(response.get('updated_at', '').replace('Z', '+00:00')),
                merged_at=datetime.fromisoformat(response.get('merged_at', '').replace('Z', '+00:00')) if response.get('merged_at') else None,
                mergeable=response.get('mergeable'),
                draft=response.get('draft', False),
                commits=response.get('commits', 0),
                additions=response.get('additions', 0),
                deletions=response.get('deletions', 0),
                changed_files=response.get('changed_files', 0)
            )
            
            self.pull_requests[pr_number] = pr
            await self._store_pull_request(pr)
            
        except Exception as e:
            logger.error(f"Failed to fetch PR info for #{pr_number}: {e}")
    
    # Public utility methods
    
    def get_repository_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        return {
            'total_commits': len([f for f in Path(self.local_repo_path).rglob('.git')]),
            'total_pull_requests': len(self.pull_requests),
            'total_issues': len(self.issues),
            'total_test_runs': len(self.test_runs),
            'current_branch': self.git_ops.get_current_branch(),
            'modified_files': len(self.git_ops.get_modified_files())
        }
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get test execution summary."""
        if not self.test_runs:
            return {'no_tests': True}
        
        recent_runs = sorted(self.test_runs.values(), key=lambda x: x.started_at, reverse=True)[:10]
        
        total_tests = sum(run.total_tests for run in recent_runs)
        total_passed = sum(run.passed_tests for run in recent_runs)
        total_failed = sum(run.failed_tests for run in recent_runs)
        
        return {
            'recent_runs': len(recent_runs),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'success_rate': total_passed / total_tests if total_tests > 0 else 0,
            'latest_run': asdict(recent_runs[0]) if recent_runs else None
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up GitHubIntegration")
        
        if self.api_client:
            await self.api_client.close()