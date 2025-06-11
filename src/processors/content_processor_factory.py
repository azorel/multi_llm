#!/usr/bin/env python3
"""
Content Processor Factory
=========================

Factory for creating content processors for different types (YouTube, GitHub, Obsidian, Markdown).
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from youtube_processor import YouTubeProcessor
from loguru import logger


class ContentProcessor(ABC):
    """Abstract base class for content processors."""
    
    @abstractmethod
    async def can_process(self, url: str, content_type: str) -> bool:
        """Check if this processor can handle the given URL/content type."""
        pass
    
    @abstractmethod
    async def process_content(self, url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process the content and return structured data."""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> list:
        """Get list of supported content types."""
        pass


class YouTubeContentProcessor(ContentProcessor):
    """Processor for YouTube videos."""
    
    def __init__(self):
        self.youtube_processor = YouTubeProcessor()
    
    async def can_process(self, url: str, content_type: str) -> bool:
        """Check if this is a YouTube URL."""
        return (content_type.lower() == "youtube" or 
                "youtube.com" in url.lower() or 
                "youtu.be" in url.lower())
    
    async def process_content(self, url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process YouTube video."""
        logger.info(f"🎬 Processing YouTube video: {url}")
        return await self.youtube_processor.process_video(url)
    
    def get_supported_types(self) -> list:
        return ["YouTube"]


class GitHubContentProcessor(ContentProcessor):
    """Processor for GitHub repositories."""
    
    def __init__(self):
        self.supported_extensions = {'.md', '.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yaml', '.yml', '.txt'}
    
    async def can_process(self, url: str, content_type: str) -> bool:
        """Check if this is a GitHub URL."""
        return (content_type.lower() == "github" or 
                "github.com" in url.lower())
    
    async def process_content(self, url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process GitHub repository."""
        logger.info(f"📂 Processing GitHub repository: {url}")
        
        try:
            # Extract repo info from URL
            repo_info = self._parse_github_url(url)
            if not repo_info:
                return {"error": "Invalid GitHub URL format"}
            
            # Get repository metadata
            repo_metadata = await self._get_repo_metadata(repo_info)
            
            # Analyze repository structure
            repo_analysis = await self._analyze_repository(repo_info)
            
            # Generate insights
            insights = await self._generate_repo_insights(repo_metadata, repo_analysis)
            
            return {
                "success": True,
                "url": url,
                "content_type": "GitHub",
                "metadata": repo_metadata,
                "analysis": repo_analysis,
                "knowledge_hub": {
                    "ai_summary": self._generate_repo_summary(repo_metadata, repo_analysis),
                    "content_category": self._categorize_repo(repo_metadata, repo_analysis),
                    "difficulty_level": self._assess_repo_difficulty(repo_analysis),
                    "implementation_time": self._estimate_implementation_time(repo_analysis),
                    "hashtags": self._generate_repo_hashtags(repo_metadata, repo_analysis),
                    "key_insights": insights.get("key_insights", []),
                    "action_items": insights.get("action_items", []),
                    "relevance_indicators": insights.get("relevance_indicators", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing GitHub repository: {e}")
            return {"error": str(e)}
    
    def _parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub URL to extract owner and repo."""
        try:
            if "github.com" not in url:
                return None
            
            # Handle different GitHub URL formats
            if "/tree/" in url or "/blob/" in url:
                # Extract base repo URL
                parts = url.split("/tree/")[0].split("/blob/")[0]
            else:
                parts = url.rstrip('/')
            
            path_parts = parts.split("github.com/")[1].split("/")
            
            if len(path_parts) >= 2:
                return {
                    "owner": path_parts[0],
                    "repo": path_parts[1],
                    "full_name": f"{path_parts[0]}/{path_parts[1]}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing GitHub URL: {e}")
            return None
    
    async def _get_repo_metadata(self, repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Get repository metadata from GitHub API."""
        try:
            import requests
            
            api_url = f"https://api.github.com/repos/{repo_info['full_name']}"
            
            response = requests.get(api_url, timeout=10)
            
            if response.status_code == 200:
                repo_data = response.json()
                
                return {
                    "name": repo_data.get("name", ""),
                    "full_name": repo_data.get("full_name", ""),
                    "description": repo_data.get("description", ""),
                    "language": repo_data.get("language", ""),
                    "languages_url": repo_data.get("languages_url", ""),
                    "stars": repo_data.get("stargazers_count", 0),
                    "forks": repo_data.get("forks_count", 0),
                    "watchers": repo_data.get("watchers_count", 0),
                    "size": repo_data.get("size", 0),
                    "topics": repo_data.get("topics", []),
                    "license": repo_data.get("license", {}).get("name", "None") if repo_data.get("license") else "None",
                    "created_at": repo_data.get("created_at", ""),
                    "updated_at": repo_data.get("updated_at", ""),
                    "homepage": repo_data.get("homepage", ""),
                    "archived": repo_data.get("archived", False),
                    "private": repo_data.get("private", False)
                }
            else:
                return {"error": f"GitHub API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error getting repo metadata: {e}")
            return {"error": str(e)}
    
    async def _analyze_repository(self, repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze repository structure and content."""
        try:
            import requests
            
            analysis = {
                "languages": {},
                "file_structure": {},
                "readme_content": "",
                "has_docs": False,
                "has_tests": False,
                "framework_indicators": [],
                "complexity_score": 0
            }
            
            # Get languages
            languages_url = f"https://api.github.com/repos/{repo_info['full_name']}/languages"
            response = requests.get(languages_url, timeout=10)
            
            if response.status_code == 200:
                analysis["languages"] = response.json()
            
            # Get repository contents
            contents_url = f"https://api.github.com/repos/{repo_info['full_name']}/contents"
            response = requests.get(contents_url, timeout=10)
            
            if response.status_code == 200:
                contents = response.json()
                
                for item in contents:
                    name = item.get("name", "").lower()
                    item_type = item.get("type", "")
                    
                    analysis["file_structure"][name] = item_type
                    
                    # Check for important files
                    if name in ["readme.md", "readme.txt", "readme"]:
                        # Get README content
                        readme_content = await self._get_file_content(repo_info, item.get("path", ""))
                        analysis["readme_content"] = readme_content[:2000]  # First 2000 chars
                    
                    elif name in ["docs", "documentation"]:
                        analysis["has_docs"] = True
                    
                    elif "test" in name or name in ["tests", "spec", "__tests__"]:
                        analysis["has_tests"] = True
                    
                    # Framework detection
                    framework_files = {
                        "package.json": "Node.js/JavaScript",
                        "requirements.txt": "Python",
                        "pyproject.toml": "Python",
                        "cargo.toml": "Rust",
                        "pom.xml": "Java/Maven",
                        "build.gradle": "Java/Gradle",
                        "composer.json": "PHP",
                        "gemfile": "Ruby",
                        "dockerfile": "Docker"
                    }
                    
                    if name in framework_files:
                        analysis["framework_indicators"].append(framework_files[name])
            
            # Calculate complexity score
            analysis["complexity_score"] = self._calculate_complexity_score(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            return {"error": str(e)}
    
    async def _get_file_content(self, repo_info: Dict[str, str], file_path: str) -> str:
        """Get content of a specific file."""
        try:
            import requests
            import base64
            
            file_url = f"https://api.github.com/repos/{repo_info['full_name']}/contents/{file_path}"
            response = requests.get(file_url, timeout=10)
            
            if response.status_code == 200:
                file_data = response.json()
                
                if file_data.get("encoding") == "base64":
                    content = base64.b64decode(file_data.get("content", "")).decode("utf-8")
                    return content
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return ""
    
    def _calculate_complexity_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate repository complexity score (1-10)."""
        score = 1
        
        # Language diversity
        lang_count = len(analysis.get("languages", {}))
        score += min(lang_count, 3)
        
        # Documentation presence
        if analysis.get("has_docs"):
            score += 1
        if analysis.get("readme_content"):
            score += 1
        
        # Testing presence
        if analysis.get("has_tests"):
            score += 1
        
        # Framework complexity
        frameworks = analysis.get("framework_indicators", [])
        score += min(len(frameworks), 2)
        
        # File structure complexity
        file_count = len(analysis.get("file_structure", {}))
        if file_count > 20:
            score += 1
        if file_count > 50:
            score += 1
        
        return min(score, 10)
    
    def _generate_repo_summary(self, metadata: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate AI summary for GitHub repository."""
        try:
            parts = []
            
            # Basic info
            name = metadata.get("name", "Unknown")
            description = metadata.get("description", "No description")
            language = metadata.get("language", "Unknown")
            stars = metadata.get("stars", 0)
            
            parts.append(f"📂 **{name}**")
            parts.append(f"🔧 Primary Language: {language}")
            parts.append(f"⭐ Stars: {stars:,} | 🍴 Forks: {metadata.get('forks', 0):,}")
            
            if description:
                parts.append(f"\n📝 **Description:**\n{description}")
            
            # Languages breakdown
            languages = analysis.get("languages", {})
            if languages:
                total_bytes = sum(languages.values())
                lang_percentages = []
                for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:3]:
                    percentage = (bytes_count / total_bytes) * 100
                    lang_percentages.append(f"{lang} ({percentage:.1f}%)")
                
                parts.append(f"\n💻 **Languages:** {', '.join(lang_percentages)}")
            
            # Repository insights
            insights = []
            if analysis.get("has_docs"):
                insights.append("📚 Well-documented")
            if analysis.get("has_tests"):
                insights.append("🧪 Has tests")
            
            frameworks = analysis.get("framework_indicators", [])
            if frameworks:
                insights.append(f"🔧 Framework: {', '.join(set(frameworks))}")
            
            complexity = analysis.get("complexity_score", 0)
            if complexity >= 7:
                insights.append("🔥 Complex project")
            elif complexity >= 4:
                insights.append("⚡ Moderate complexity")
            else:
                insights.append("🌱 Simple project")
            
            if insights:
                parts.append(f"\n🔍 **Insights:** {' | '.join(insights)}")
            
            # README preview
            readme = analysis.get("readme_content", "")
            if readme:
                preview = readme[:200] + "..." if len(readme) > 200 else readme
                parts.append(f"\n📖 **README Preview:**\n{preview}")
            
            license_info = metadata.get("license", "None")
            if license_info != "None":
                parts.append(f"\n📄 **License:** {license_info}")
            
            return "\n".join(parts)
            
        except Exception as e:
            logger.error(f"Error generating repo summary: {e}")
            return f"📂 GitHub Repository: {metadata.get('name', 'Unknown')}"
    
    def _categorize_repo(self, metadata: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Categorize repository by content."""
        description = metadata.get("description", "").lower()
        topics = metadata.get("topics", [])
        language = metadata.get("language", "").lower()
        
        # AI/ML keywords
        ai_keywords = ["ai", "machine learning", "neural", "deep learning", "tensorflow", "pytorch", "model"]
        if any(keyword in description for keyword in ai_keywords) or any(keyword in topics for keyword in ai_keywords):
            return "AI & Automation"
        
        # Web development
        web_keywords = ["web", "frontend", "backend", "react", "vue", "angular", "node"]
        if language in ["javascript", "typescript", "html", "css"] or any(keyword in description for keyword in web_keywords):
            return "Technology"
        
        # Business/productivity tools
        business_keywords = ["business", "productivity", "management", "workflow", "automation"]
        if any(keyword in description for keyword in business_keywords):
            return "Business"
        
        # Development tools
        dev_keywords = ["tool", "utility", "framework", "library", "sdk", "api"]
        if any(keyword in description for keyword in dev_keywords):
            return "Technology"
        
        return "Technology"  # Default
    
    def _assess_repo_difficulty(self, analysis: Dict[str, Any]) -> str:
        """Assess repository difficulty level."""
        complexity = analysis.get("complexity_score", 0)
        
        if complexity >= 7:
            return "Advanced"
        elif complexity >= 4:
            return "Intermediate"
        else:
            return "Beginner"
    
    def _estimate_implementation_time(self, analysis: Dict[str, Any]) -> str:
        """Estimate implementation/understanding time."""
        complexity = analysis.get("complexity_score", 0)
        file_count = len(analysis.get("file_structure", {}))
        
        if complexity >= 7 or file_count > 50:
            return "Long (> 4h)"
        elif complexity >= 4 or file_count > 20:
            return "Medium (1-4h)"
        else:
            return "Quick (< 1h)"
    
    def _generate_repo_hashtags(self, metadata: Dict[str, Any], analysis: Dict[str, Any]) -> list:
        """Generate hashtags for repository."""
        hashtags = {"#github", "#development"}
        
        # Language-based tags
        language = metadata.get("language", "").lower()
        lang_tags = {
            "python": "#python",
            "javascript": "#javascript",
            "typescript": "#typescript",
            "rust": "#rust",
            "go": "#golang",
            "java": "#java",
            "c++": "#cpp"
        }
        
        if language in lang_tags:
            hashtags.add(lang_tags[language])
        
        # Framework tags
        frameworks = analysis.get("framework_indicators", [])
        for framework in frameworks:
            if "node" in framework.lower():
                hashtags.add("#nodejs")
            elif "python" in framework.lower():
                hashtags.add("#python")
            elif "docker" in framework.lower():
                hashtags.add("#docker")
        
        # Topic-based tags
        topics = metadata.get("topics", [])
        for topic in topics[:3]:  # First 3 topics
            hashtags.add(f"#{topic}")
        
        # Content-based tags
        description = metadata.get("description", "").lower()
        if any(word in description for word in ["api", "rest", "graphql"]):
            hashtags.add("#api")
        if any(word in description for word in ["ai", "ml", "machine learning"]):
            hashtags.add("#ai")
        if any(word in description for word in ["web", "frontend", "backend"]):
            hashtags.add("#web")
        
        return list(hashtags)[:8]  # Limit to 8 tags
    
    async def _generate_repo_insights(self, metadata: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights from repository analysis."""
        insights = {
            "key_insights": [],
            "action_items": [],
            "relevance_indicators": []
        }
        
        # Key insights
        stars = metadata.get("stars", 0)
        if stars > 1000:
            insights["key_insights"].append(f"Popular project with {stars:,} stars")
        
        if analysis.get("has_tests"):
            insights["key_insights"].append("Well-tested codebase")
        
        if analysis.get("has_docs"):
            insights["key_insights"].append("Well-documented project")
        
        complexity = analysis.get("complexity_score", 0)
        if complexity >= 7:
            insights["key_insights"].append("Complex, feature-rich project")
        
        # Action items
        if not analysis.get("has_tests"):
            insights["action_items"].append("Consider adding tests if contributing")
        
        if metadata.get("language"):
            insights["action_items"].append(f"Review {metadata['language']} code structure")
        
        if analysis.get("readme_content"):
            insights["action_items"].append("Read README for setup instructions")
        
        # Relevance indicators
        if stars > 500:
            insights["relevance_indicators"].append("High Priority")
        
        if analysis.get("has_docs"):
            insights["relevance_indicators"].append("Learning")
        
        if "framework" in metadata.get("description", "").lower():
            insights["relevance_indicators"].append("Implementation")
        
        insights["relevance_indicators"].append("Reference")
        
        return insights
    
    def get_supported_types(self) -> list:
        return ["GitHub"]


class ObsidianContentProcessor(ContentProcessor):
    """Processor for Obsidian vaults and Markdown files."""
    
    async def can_process(self, url: str, content_type: str) -> bool:
        """Check if this is Obsidian or Markdown content."""
        return content_type.lower() in ["obsidian", "markdown"]
    
    async def process_content(self, url: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process Obsidian/Markdown content."""
        logger.info(f"📝 Processing Markdown/Obsidian content: {url}")
        
        try:
            # For now, return basic structure
            # This can be enhanced to parse actual Obsidian vaults or markdown files
            
            return {
                "success": True,
                "url": url,
                "content_type": "Markdown",
                "metadata": {
                    "title": "Markdown/Obsidian Content",
                    "content_type": "text/markdown"
                },
                "knowledge_hub": {
                    "ai_summary": f"📝 **Markdown/Obsidian Content**\n\n🔗 Source: {url}\n\n📄 This is a markdown document or Obsidian vault entry.",
                    "content_category": "Documentation",
                    "difficulty_level": "Beginner",
                    "implementation_time": "Quick (< 1h)",
                    "hashtags": ["#markdown", "#documentation", "#notes"],
                    "relevance_indicators": ["Reference", "Learning"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing Markdown/Obsidian content: {e}")
            return {"error": str(e)}
    
    def get_supported_types(self) -> list:
        return ["Obsidian", "Markdown"]


class ContentProcessorFactory:
    """Factory for creating content processors."""
    
    def __init__(self):
        self.processors = [
            YouTubeContentProcessor(),
            GitHubContentProcessor(),
            ObsidianContentProcessor()
        ]
    
    async def get_processor(self, url: str, content_type: str) -> Optional[ContentProcessor]:
        """Get appropriate processor for the content type."""
        for processor in self.processors:
            if await processor.can_process(url, content_type):
                return processor
        
        return None
    
    def get_supported_types(self) -> list:
        """Get all supported content types."""
        types = []
        for processor in self.processors:
            types.extend(processor.get_supported_types())
        return types
    
    async def process_content(self, url: str, content_type: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process content using appropriate processor."""
        processor = await self.get_processor(url, content_type)
        
        if not processor:
            return {
                "error": f"No processor available for content type: {content_type}",
                "supported_types": self.get_supported_types()
            }
        
        return await processor.process_content(url, metadata)


# Factory instance
content_factory = ContentProcessorFactory()