#!/usr/bin/env python3
"""
Sequential Thinking MCP Client Integration
==========================================

Client for interacting with the Sequential Thinking MCP server.
Provides structured, step-by-step problem-solving capabilities to the autonomous agent system.
"""

import json
import asyncio
import subprocess
import os
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
from pathlib import Path


@dataclass
class ThoughtStep:
    """Represents a single thought step in the sequential thinking process."""
    thought: str
    thought_number: int
    total_thoughts: int
    next_thought_needed: bool
    is_revision: bool = False
    revises_thought: Optional[int] = None
    branch_from_thought: Optional[int] = None
    branch_id: Optional[str] = None
    needs_more_thoughts: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ThinkingSession:
    """Represents a complete thinking session with multiple thought steps."""
    session_id: str
    problem_description: str
    thought_steps: List[ThoughtStep] = field(default_factory=list)
    branches: Dict[str, List[ThoughtStep]] = field(default_factory=dict)
    final_solution: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class SequentialThinkingClient:
    """
    Client for interacting with the Sequential Thinking MCP server.
    
    Provides a Python interface to the sequential thinking tools for
    structured problem-solving and analysis.
    """
    
    def __init__(self, server_path: Optional[str] = None):
        """Initialize the Sequential Thinking MCP client."""
        self.server_path = server_path or self._get_default_server_path()
        self.mcp_command = ["node", self.server_path]
        self.active_sessions: Dict[str, ThinkingSession] = {}
        
        # Ensure the server is built
        self._ensure_server_built()
    
    def _get_default_server_path(self) -> str:
        """Get the default path to the sequential thinking server."""
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / "mcp-servers" / "sequential-thinking" / "dist" / "index.js")
    
    def _ensure_server_built(self):
        """Ensure the TypeScript server is built."""
        server_dir = Path(self.server_path).parent.parent
        
        if not (server_dir / "dist" / "index.js").exists():
            logger.info("Building Sequential Thinking MCP server...")
            try:
                subprocess.run(
                    ["npm", "install"],
                    cwd=server_dir,
                    check=True,
                    capture_output=True
                )
                subprocess.run(
                    ["npm", "run", "build"],
                    cwd=server_dir,
                    check=True,
                    capture_output=True
                )
                logger.success("Sequential Thinking MCP server built successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to build Sequential Thinking MCP server: {e}")
                raise
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result."""
        try:
            # Prepare the MCP request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Execute the MCP server
            process = await asyncio.create_subprocess_exec(
                *self.mcp_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Send request and get response
            stdout, stderr = await process.communicate(
                input=json.dumps(request).encode()
            )
            
            if process.returncode != 0:
                logger.error(f"MCP tool call failed: {stderr.decode()}")
                return {"error": f"MCP process failed: {stderr.decode()}"}
            
            # Parse response
            response = json.loads(stdout.decode())
            
            if "error" in response:
                logger.error(f"MCP tool error: {response['error']}")
                return {"error": response["error"]}
            
            return response.get("result", {})
            
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def start_thinking_session(self, problem_description: str) -> str:
        """Start a new thinking session for a problem."""
        session_id = str(uuid.uuid4())
        session = ThinkingSession(
            session_id=session_id,
            problem_description=problem_description
        )
        self.active_sessions[session_id] = session
        
        logger.info(f"Started thinking session {session_id} for: {problem_description[:100]}...")
        return session_id
    
    async def add_thought_step(
        self,
        session_id: str,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        next_thought_needed: bool,
        is_revision: bool = False,
        revises_thought: Optional[int] = None,
        branch_from_thought: Optional[int] = None,
        branch_id: Optional[str] = None,
        needs_more_thoughts: bool = False
    ) -> Dict[str, Any]:
        """Add a thought step to a thinking session."""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Prepare arguments for the MCP tool
        arguments = {
            "thought": thought,
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
            "nextThoughtNeeded": next_thought_needed
        }
        
        # Add optional parameters
        if is_revision:
            arguments["isRevision"] = is_revision
        if revises_thought is not None:
            arguments["revisesThought"] = revises_thought
        if branch_from_thought is not None:
            arguments["branchFromThought"] = branch_from_thought
        if branch_id is not None:
            arguments["branchId"] = branch_id
        if needs_more_thoughts:
            arguments["needsMoreThoughts"] = needs_more_thoughts
        
        # Call the MCP tool
        result = await self._call_mcp_tool("sequentialthinking", arguments)
        
        if "error" in result:
            logger.error(f"Error in thought step: {result['error']}")
            return result
        
        # Create and store the thought step
        thought_step = ThoughtStep(
            thought=thought,
            thought_number=thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=next_thought_needed,
            is_revision=is_revision,
            revises_thought=revises_thought,
            branch_from_thought=branch_from_thought,
            branch_id=branch_id,
            needs_more_thoughts=needs_more_thoughts
        )
        
        session = self.active_sessions[session_id]
        session.thought_steps.append(thought_step)
        
        # Handle branching
        if branch_id and branch_from_thought:
            if branch_id not in session.branches:
                session.branches[branch_id] = []
            session.branches[branch_id].append(thought_step)
        
        logger.debug(f"Added thought step {thought_number}/{total_thoughts} to session {session_id}")
        
        return result
    
    async def complete_thinking_session(self, session_id: str, final_solution: str) -> ThinkingSession:
        """Complete a thinking session with a final solution."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.final_solution = final_solution
        session.completed_at = datetime.now()
        
        logger.info(f"Completed thinking session {session_id}")
        return session
    
    async def get_thinking_session(self, session_id: str) -> Optional[ThinkingSession]:
        """Get a thinking session by ID."""
        return self.active_sessions.get(session_id)
    
    async def solve_problem_step_by_step(
        self,
        problem_description: str,
        initial_thought_estimate: int = 5,
        max_thoughts: int = 20
    ) -> ThinkingSession:
        """
        Solve a problem using structured step-by-step thinking.
        
        This is a high-level method that handles the full thinking process.
        """
        session_id = await self.start_thinking_session(problem_description)
        
        # Initial analysis
        thought_count = 1
        total_thoughts = initial_thought_estimate
        
        # Start with problem analysis
        await self.add_thought_step(
            session_id=session_id,
            thought=f"Let me analyze this problem: {problem_description}",
            thought_number=thought_count,
            total_thoughts=total_thoughts,
            next_thought_needed=True
        )
        
# DEMO CODE REMOVED: # For demonstration, we'll simulate a thinking process
        # In practice, this would be driven by the LLM using the thinking tool
        thought_count += 1
        
        await self.add_thought_step(
            session_id=session_id,
            thought="Breaking down the problem into key components and identifying what needs to be solved.",
            thought_number=thought_count,
            total_thoughts=total_thoughts,
            next_thought_needed=True
        )
        
        thought_count += 1
        
        await self.add_thought_step(
            session_id=session_id,
            thought="Considering different approaches and their potential effectiveness.",
            thought_number=thought_count,
            total_thoughts=total_thoughts,
            next_thought_needed=True
        )
        
        thought_count += 1
        
        await self.add_thought_step(
            session_id=session_id,
            thought="Selecting the most promising approach and outlining implementation steps.",
            thought_number=thought_count,
            total_thoughts=total_thoughts,
            next_thought_needed=True
        )
        
        thought_count += 1
        
        await self.add_thought_step(
            session_id=session_id,
            thought="Finalizing the solution and ensuring all requirements are addressed.",
            thought_number=thought_count,
            total_thoughts=total_thoughts,
            next_thought_needed=False
        )
        
        # Complete the session
        final_solution = "Solution completed through structured thinking process."
        return await self.complete_thinking_session(session_id, final_solution)
    
    async def revise_thought(
        self,
        session_id: str,
        original_thought_number: int,
        revised_thought: str,
        new_total_thoughts: Optional[int] = None
    ) -> Dict[str, Any]:
        """Revise a previous thought in the thinking process."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Find the original thought
        original_thought = None
        for step in session.thought_steps:
            if step.thought_number == original_thought_number:
                original_thought = step
                break
        
        if not original_thought:
            raise ValueError(f"Thought {original_thought_number} not found in session")
        
        # Determine new thought number and total
        next_thought_number = len(session.thought_steps) + 1
        total_thoughts = new_total_thoughts or original_thought.total_thoughts
        
        return await self.add_thought_step(
            session_id=session_id,
            thought=revised_thought,
            thought_number=next_thought_number,
            total_thoughts=total_thoughts,
            next_thought_needed=True,
            is_revision=True,
            revises_thought=original_thought_number
        )
    
    async def create_thought_branch(
        self,
        session_id: str,
        branch_from_thought_number: int,
        branch_thought: str,
        branch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new branch in the thinking process."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if branch_id is None:
            branch_id = f"branch_{uuid.uuid4().hex[:8]}"
        
        # Determine new thought number
        next_thought_number = len(session.thought_steps) + 1
        
        return await self.add_thought_step(
            session_id=session_id,
            thought=branch_thought,
            thought_number=next_thought_number,
            total_thoughts=next_thought_number + 2,  # Estimate a few more thoughts needed
            next_thought_needed=True,
            branch_from_thought=branch_from_thought_number,
            branch_id=branch_id
        )
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of a thinking session."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        return {
            "session_id": session.session_id,
            "problem_description": session.problem_description,
            "total_thoughts": len(session.thought_steps),
            "branches": list(session.branches.keys()),
            "is_completed": session.completed_at is not None,
            "final_solution": session.final_solution,
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "thought_timeline": [
                {
                    "thought_number": step.thought_number,
                    "thought": step.thought[:100] + "..." if len(step.thought) > 100 else step.thought,
                    "is_revision": step.is_revision,
                    "branch_id": step.branch_id,
                    "timestamp": step.timestamp.isoformat()
                }
                for step in session.thought_steps
            ]
        }
    
    async def test_connection(self) -> bool:
        """Test if the connection to the Sequential Thinking MCP server is working."""
        try:
            # Test with a simple thought
            result = await self._call_mcp_tool("sequentialthinking", {
                "thought": "Testing connection to sequential thinking server",
                "thoughtNumber": 1,
                "totalThoughts": 1,
                "nextThoughtNeeded": False
            })
            
            return "error" not in result
            
        except Exception as e:
            logger.error(f"Sequential Thinking MCP connection test failed: {e}")
            return False
    
    def list_active_sessions(self) -> List[str]:
        """List all active thinking session IDs."""
        return list(self.active_sessions.keys())
    
    async def cleanup_session(self, session_id: str) -> bool:
        """Remove a thinking session from memory."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.debug(f"Cleaned up thinking session {session_id}")
            return True
        return False


# Factory function for easy integration
def create_sequential_thinking_client(server_path: Optional[str] = None) -> SequentialThinkingClient:
    """Create a Sequential Thinking MCP client instance."""
    return SequentialThinkingClient(server_path)