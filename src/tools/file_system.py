import os
import re
import shutil
import tempfile
import hashlib
import gzip
import json
import uuid
import asyncio
import aiofiles
import stat
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
from cryptography.fernet import Fernet
from loguru import logger
import magic  # python-magic for file type detection
import psutil  # for resource monitoring


class FileOperation(Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    COPY = "copy"
    MOVE = "move"


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class FileSystemStats:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    bytes_read: int = 0
    bytes_written: int = 0
    files_created: int = 0
    files_deleted: int = 0
    security_violations: int = 0
    last_operation: Optional[datetime] = None


@dataclass
class SandboxConfig:
    max_files: int = 1000
    max_total_size: int = 100 * 1024 * 1024  # 100MB
    max_file_size: int = 10 * 1024 * 1024   # 10MB
    allowed_extensions: Set[str] = field(default_factory=lambda: {
        '.txt', '.json', '.yaml', '.yml', '.md', '.py', '.js', '.ts',
        '.html', '.css', '.xml', '.csv', '.log'
    })
    blocked_extensions: Set[str] = field(default_factory=lambda: {
        '.exe', '.bat', '.cmd', '.scr', '.dll', '.sys', '.bin'
    })
    auto_cleanup_hours: int = 24


@dataclass
class AuditLogEntry:
    timestamp: datetime
    operation: FileOperation
    path: str
    user_id: Optional[str]
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileTransaction:
    transaction_id: str
    operations: List[Dict[str, Any]] = field(default_factory=list)
    rollback_data: List[Dict[str, Any]] = field(default_factory=list)
    committed: bool = False
    rolled_back: bool = False


class MaliciousPatternDetector:
    """Detect malicious patterns in file content and names."""
    
    def __init__(self):
        # Malicious file patterns
        self.malicious_patterns = [
            # Command injection patterns
            r';\s*(rm|del|format|shutdown|reboot)',
            r'\|\s*(curl|wget|nc|netcat)',
            r'`[^`]*`',  # Command substitution
            r'\$\([^)]*\)',  # Command substitution
            
            # Script injection patterns
            r'<script[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'eval\s*\(',
            r'exec\s*\(',
            
            # Path traversal patterns
            r'\.\.[\\/]',
            r'[\\/]\.\.[\\/]',
            
            # Suspicious file operations
            r'(open|write|delete|remove)\s*\([^)]*["\'][\\/]',
            
            # Network activity patterns
            r'(socket|urllib|requests|http)\.',
            r'(ftp|ssh|telnet|smtp):\/\/',
            
            # Encoded content patterns
            r'base64\s*\.',
            r'fromhex\s*\(',
            r'decode\s*\(["\']base64',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.malicious_patterns]
        
        # Suspicious filename patterns
        self.suspicious_names = [
            r'^\.ht',  # .htaccess, .htpasswd
            r'passwd$',
            r'shadow$',
            r'id_rsa',
            r'private.*key',
            r'\.key$',
            r'\.pem$',
            r'config.*\.php$',
        ]
        
        self.compiled_name_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_names]

    def scan_content(self, content: str) -> List[str]:
        """Scan content for malicious patterns."""
        detected_patterns = []
        
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(content):
                detected_patterns.append(f"Malicious pattern {i+1}: {self.malicious_patterns[i]}")
        
        return detected_patterns

    def scan_filename(self, filename: str) -> List[str]:
        """Scan filename for suspicious patterns."""
        detected_patterns = []
        
        for i, pattern in enumerate(self.compiled_name_patterns):
            if pattern.search(filename):
                detected_patterns.append(f"Suspicious filename pattern {i+1}: {self.suspicious_names[i]}")
        
        return detected_patterns


class SecureFileSystemManager:
    """Comprehensive secure file system manager with sandboxing and security features."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Base configuration
        self.base_path = Path(config.get("base_path", "./sandbox"))
        self.security_level = SecurityLevel(config.get("security_level", "medium"))
        
        # Sandbox configuration
        self.sandbox_config = SandboxConfig(
            max_files=config.get("max_files", 1000),
            max_total_size=config.get("max_total_size", 100 * 1024 * 1024),
            max_file_size=config.get("max_file_size", 10 * 1024 * 1024),
            auto_cleanup_hours=config.get("auto_cleanup_hours", 24)
        )
        
        # Security components
        self.pattern_detector = MaliciousPatternDetector()
        self.encryption_enabled = config.get("encryption_enabled", False)
        self.compression_enabled = config.get("compression_enabled", False)
        
        # Encryption setup
        if self.encryption_enabled:
            self.encryption_key = config.get("encryption_key")
            if not self.encryption_key:
                self.encryption_key = Fernet.generate_key()
            self.cipher_suite = Fernet(self.encryption_key)
        
        # Statistics and monitoring
        self.stats = FileSystemStats()
        self.audit_log = deque(maxlen=10000)
        self.resource_monitor = config.get("resource_monitor", True)
        
        # Transaction management
        self.transactions = {}
        self.transaction_lock = asyncio.Lock()
        
        # File watching
        self.file_watchers = {}
        self.watch_callbacks = defaultdict(list)
        
        # Thread safety
        self.operation_lock = threading.RLock()
        
        # Initialize base directories
        self._initialize_directories()
        
        logger.info(f"SecureFileSystemManager initialized with security level: {self.security_level.value}")

    def _initialize_directories(self):
        """Initialize required directories."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "sandboxes").mkdir(exist_ok=True)
        (self.base_path / "temp").mkdir(exist_ok=True)
        (self.base_path / "backups").mkdir(exist_ok=True)
        (self.base_path / "audit").mkdir(exist_ok=True)

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Validate and normalize file path with security checks."""
        path = Path(path)
        
        # Convert to absolute path
        if not path.is_absolute():
            path = self.base_path / path
        
        # Resolve any symlinks and relative paths
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError):
            raise ValueError(f"Invalid path: {path}")
        
        # Ensure path is within base directory (prevent path traversal)
        try:
            resolved_path.relative_to(self.base_path.resolve())
        except ValueError:
            raise ValueError(f"Path outside sandbox: {path}")
        
        # Check for suspicious path components
        for part in resolved_path.parts:
            if part.startswith('.') and part not in ['.', '..']:
                if self.security_level in [SecurityLevel.HIGH, SecurityLevel.MAXIMUM]:
                    raise ValueError(f"Hidden files not allowed: {part}")
        
        return resolved_path

    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security issues."""
        # Check for suspicious patterns
        suspicious_patterns = self.pattern_detector.scan_filename(filename)
        if suspicious_patterns and self.security_level != SecurityLevel.LOW:
            raise ValueError(f"Suspicious filename detected: {suspicious_patterns}")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        
        if file_ext in self.sandbox_config.blocked_extensions:
            raise ValueError(f"Blocked file extension: {file_ext}")
        
        if (self.security_level in [SecurityLevel.HIGH, SecurityLevel.MAXIMUM] and 
            file_ext not in self.sandbox_config.allowed_extensions):
            raise ValueError(f"File extension not in whitelist: {file_ext}")
        
        return True

    def _validate_content(self, content: Union[str, bytes]) -> bool:
        """Validate file content for malicious patterns."""
        if isinstance(content, bytes):
            try:
                content_str = content.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                # Binary content - use magic for type detection
                if self.security_level in [SecurityLevel.HIGH, SecurityLevel.MAXIMUM]:
                    file_type = magic.from_buffer(content, mime=True)
                    allowed_types = ['text/', 'application/json', 'application/xml']
                    if not any(file_type.startswith(t) for t in allowed_types):
                        raise ValueError(f"Binary file type not allowed: {file_type}")
                return True
        else:
            content_str = content
        
        # Scan for malicious patterns
        if self.security_level != SecurityLevel.LOW:
            malicious_patterns = self.pattern_detector.scan_content(content_str)
            if malicious_patterns:
                raise ValueError(f"Malicious content detected: {malicious_patterns}")
        
        return True

    def _check_resource_limits(self, sandbox_path: Optional[Path] = None) -> bool:
        """Check if operation would exceed resource limits."""
        if not self.resource_monitor:
            return True
        
        check_path = sandbox_path or self.base_path
        
        # Count files and total size
        file_count = 0
        total_size = 0
        
        try:
            for item in check_path.rglob('*'):
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
        except (OSError, PermissionError):
            logger.warning(f"Could not check resource limits for {check_path}")
            return True
        
        # Check limits
        if file_count >= self.sandbox_config.max_files:
            raise ValueError(f"File count limit exceeded: {file_count}/{self.sandbox_config.max_files}")
        
        if total_size >= self.sandbox_config.max_total_size:
            raise ValueError(f"Size limit exceeded: {total_size}/{self.sandbox_config.max_total_size}")
        
        return True

    def _log_operation(self, operation: FileOperation, path: str, success: bool, 
                      error_message: Optional[str] = None, **metadata):
        """Log file system operation for audit."""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            operation=operation,
            path=path,
            user_id=metadata.get('user_id'),
            success=success,
            error_message=error_message,
            metadata=metadata
        )
        
        self.audit_log.append(entry)
        
        # Update statistics
        self.stats.total_operations += 1
        if success:
            self.stats.successful_operations += 1
        else:
            self.stats.failed_operations += 1
            if "security" in str(error_message).lower():
                self.stats.security_violations += 1
        
        self.stats.last_operation = datetime.now()

    async def create_file(self, path: Union[str, Path], content: Union[str, bytes], 
                         permissions: Optional[int] = None, **kwargs) -> bool:
        """Create a new file with security validation."""
        try:
            validated_path = self._validate_path(path)
            self._validate_filename(validated_path.name)
            self._validate_content(content)
            self._check_resource_limits(validated_path.parent)
            
            # Check file size limit
            content_size = len(content.encode() if isinstance(content, str) else content)
            if content_size > self.sandbox_config.max_file_size:
                raise ValueError(f"File size exceeds limit: {content_size}/{self.sandbox_config.max_file_size}")
            
            # Ensure parent directory exists
            validated_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Process content (encryption/compression)
            processed_content = await self._process_content_for_storage(content)
            
            # Atomic write operation
            temp_path = validated_path.with_suffix('.tmp')
            
            if isinstance(processed_content, str):
                async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                    await f.write(processed_content)
            else:
                async with aiofiles.open(temp_path, 'wb') as f:
                    await f.write(processed_content)
            
            # Atomic move
            temp_path.replace(validated_path)
            
            # Set permissions
            if permissions:
                validated_path.chmod(permissions)
            
            # Update statistics
            self.stats.files_created += 1
            self.stats.bytes_written += content_size
            
            self._log_operation(FileOperation.CREATE, str(validated_path), True, **kwargs)
            
            # Trigger file watchers
            await self._trigger_file_watchers(validated_path, 'created')
            
            logger.debug(f"Created file: {validated_path}")
            return True
            
        except Exception as e:
            self._log_operation(FileOperation.CREATE, str(path), False, str(e), **kwargs)
            logger.error(f"Failed to create file {path}: {e}")
            raise

    async def read_file(self, path: Union[str, Path], **kwargs) -> Union[str, bytes]:
        """Read file content with security validation."""
        try:
            validated_path = self._validate_path(path)
            
            if not validated_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            if not validated_path.is_file():
                raise ValueError(f"Not a file: {path}")
            
            # Check file size before reading
            file_size = validated_path.stat().st_size
            if file_size > self.sandbox_config.max_file_size:
                raise ValueError(f"File too large to read: {file_size}/{self.sandbox_config.max_file_size}")
            
            # Read file content
            try:
                async with aiofiles.open(validated_path, 'rb') as f:
                    raw_content = await f.read()
            except (OSError, PermissionError) as e:
                raise ValueError(f"Cannot read file: {e}")
            
            # Process content (decryption/decompression)
            content = await self._process_content_from_storage(raw_content)
            
            # Update statistics
            self.stats.bytes_read += len(raw_content)
            
            self._log_operation(FileOperation.READ, str(validated_path), True, **kwargs)
            
            logger.debug(f"Read file: {validated_path}")
            return content
            
        except Exception as e:
            self._log_operation(FileOperation.READ, str(path), False, str(e), **kwargs)
            logger.error(f"Failed to read file {path}: {e}")
            raise

    async def update_file(self, path: Union[str, Path], content: Union[str, bytes], 
                         backup: bool = True, **kwargs) -> bool:
        """Update existing file with optional backup."""
        try:
            validated_path = self._validate_path(path)
            
            if not validated_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            self._validate_content(content)
            
            # Create backup if requested
            backup_path = None
            if backup:
                backup_path = await self._create_backup(validated_path)
            
            try:
                # Check file size limit
                content_size = len(content.encode() if isinstance(content, str) else content)
                if content_size > self.sandbox_config.max_file_size:
                    raise ValueError(f"File size exceeds limit: {content_size}/{self.sandbox_config.max_file_size}")
                
                # Process content
                processed_content = await self._process_content_for_storage(content)
                
                # Atomic update
                temp_path = validated_path.with_suffix('.update_tmp')
                
                if isinstance(processed_content, str):
                    async with aiofiles.open(temp_path, 'w', encoding='utf-8') as f:
                        await f.write(processed_content)
                else:
                    async with aiofiles.open(temp_path, 'wb') as f:
                        await f.write(processed_content)
                
                # Atomic replace
                temp_path.replace(validated_path)
                
                # Update statistics
                self.stats.bytes_written += content_size
                
                self._log_operation(FileOperation.UPDATE, str(validated_path), True, 
                                  backup_created=backup_path is not None, **kwargs)
                
                # Trigger file watchers
                await self._trigger_file_watchers(validated_path, 'modified')
                
                logger.debug(f"Updated file: {validated_path}")
                return True
                
            except Exception as e:
                # Restore backup if update failed
                if backup_path and backup_path.exists():
                    backup_path.replace(validated_path)
                    logger.info(f"Restored backup after failed update: {validated_path}")
                raise
            
        except Exception as e:
            self._log_operation(FileOperation.UPDATE, str(path), False, str(e), **kwargs)
            logger.error(f"Failed to update file {path}: {e}")
            raise

    async def delete_file(self, path: Union[str, Path], secure: bool = True, **kwargs) -> bool:
        """Delete file with optional secure deletion."""
        try:
            validated_path = self._validate_path(path)
            
            if not validated_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            if not validated_path.is_file():
                raise ValueError(f"Not a file: {path}")
            
            # Create backup before deletion if secure mode
            backup_path = None
            if secure:
                backup_path = await self._create_backup(validated_path)
            
            # Secure deletion: overwrite with random data
            if secure and self.security_level in [SecurityLevel.HIGH, SecurityLevel.MAXIMUM]:
                await self._secure_delete(validated_path)
            else:
                validated_path.unlink()
            
            # Update statistics
            self.stats.files_deleted += 1
            
            self._log_operation(FileOperation.DELETE, str(validated_path), True, 
                              secure_delete=secure, backup_created=backup_path is not None, **kwargs)
            
            # Trigger file watchers
            await self._trigger_file_watchers(validated_path, 'deleted')
            
            logger.debug(f"Deleted file: {validated_path}")
            return True
            
        except Exception as e:
            self._log_operation(FileOperation.DELETE, str(path), False, str(e), **kwargs)
            logger.error(f"Failed to delete file {path}: {e}")
            raise

    async def list_directory(self, path: Union[str, Path], recursive: bool = False, 
                           include_hidden: bool = False, **kwargs) -> List[Dict[str, Any]]:
        """List directory contents with metadata."""
        try:
            validated_path = self._validate_path(path)
            
            if not validated_path.exists():
                raise FileNotFoundError(f"Directory not found: {path}")
            
            if not validated_path.is_dir():
                raise ValueError(f"Not a directory: {path}")
            
            files = []
            
            if recursive:
                pattern = '**/*'
            else:
                pattern = '*'
            
            for item in validated_path.glob(pattern):
                # Skip hidden files unless requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                try:
                    stat_info = item.stat()
                    file_info = {
                        'name': item.name,
                        'path': str(item.relative_to(self.base_path)),
                        'absolute_path': str(item),
                        'is_file': item.is_file(),
                        'is_directory': item.is_dir(),
                        'size': stat_info.st_size if item.is_file() else 0,
                        'modified': datetime.fromtimestamp(stat_info.st_mtime),
                        'created': datetime.fromtimestamp(stat_info.st_ctime),
                        'permissions': oct(stat_info.st_mode)[-3:],
                    }
                    
                    # Add file type for files
                    if item.is_file():
                        file_info['extension'] = item.suffix.lower()
                        try:
                            file_info['mime_type'] = magic.from_file(str(item), mime=True)
                        except:
                            file_info['mime_type'] = 'unknown'
                    
                    files.append(file_info)
                    
                except (OSError, PermissionError):
                    # Skip files we can't stat
                    continue
            
            self._log_operation(FileOperation.LIST, str(validated_path), True, 
                              file_count=len(files), recursive=recursive, **kwargs)
            
            logger.debug(f"Listed directory: {validated_path} ({len(files)} items)")
            return files
            
        except Exception as e:
            self._log_operation(FileOperation.LIST, str(path), False, str(e), **kwargs)
            logger.error(f"Failed to list directory {path}: {e}")
            raise

    async def create_sandbox(self, sandbox_id: Optional[str] = None) -> str:
        """Create a new isolated sandbox directory."""
        if not sandbox_id:
            sandbox_id = str(uuid.uuid4())
        
        sandbox_path = self.base_path / "sandboxes" / sandbox_id
        
        try:
            sandbox_path.mkdir(parents=True, exist_ok=False)
            
            # Create sandbox metadata
            metadata = {
                'created': datetime.now().isoformat(),
                'config': {
                    'max_files': self.sandbox_config.max_files,
                    'max_size': self.sandbox_config.max_total_size,
                    'auto_cleanup_hours': self.sandbox_config.auto_cleanup_hours
                }
            }
            
            metadata_path = sandbox_path / '.sandbox_metadata.json'
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
            
            logger.info(f"Created sandbox: {sandbox_id}")
            return sandbox_id
            
        except FileExistsError:
            raise ValueError(f"Sandbox already exists: {sandbox_id}")
        except Exception as e:
            logger.error(f"Failed to create sandbox {sandbox_id}: {e}")
            raise

    async def cleanup_sandbox(self, sandbox_id: str, force: bool = False) -> bool:
        """Clean up and remove a sandbox."""
        sandbox_path = self.base_path / "sandboxes" / sandbox_id
        
        if not sandbox_path.exists():
            raise ValueError(f"Sandbox not found: {sandbox_id}")
        
        try:
            # Check if sandbox can be cleaned up
            if not force:
                metadata_path = sandbox_path / '.sandbox_metadata.json'
                if metadata_path.exists():
                    async with aiofiles.open(metadata_path, 'r') as f:
                        metadata = json.loads(await f.read())
                    
                    created_time = datetime.fromisoformat(metadata['created'])
                    auto_cleanup_hours = metadata['config']['auto_cleanup_hours']
                    
                    if datetime.now() - created_time < timedelta(hours=auto_cleanup_hours):
                        raise ValueError(f"Sandbox too recent to cleanup (age < {auto_cleanup_hours}h)")
            
            # Remove sandbox directory
            shutil.rmtree(sandbox_path)
            
            logger.info(f"Cleaned up sandbox: {sandbox_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup sandbox {sandbox_id}: {e}")
            raise

    async def _create_backup(self, file_path: Path) -> Path:
        """Create backup of file."""
        backup_dir = self.base_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        
        logger.debug(f"Created backup: {backup_path}")
        return backup_path

    async def _secure_delete(self, file_path: Path):
        """Securely delete file by overwriting with random data."""
        file_size = file_path.stat().st_size
        
        # Overwrite with random data multiple times
        for _ in range(3):
            with open(file_path, 'rb+') as f:
                f.seek(0)
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        
        # Finally delete the file
        file_path.unlink()

    async def _process_content_for_storage(self, content: Union[str, bytes]) -> Union[str, bytes]:
        """Process content for storage (compression/encryption)."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        # Compress if enabled
        if self.compression_enabled:
            content = gzip.compress(content)
        
        # Encrypt if enabled
        if self.encryption_enabled:
            content = self.cipher_suite.encrypt(content)
        
        return content

    async def _process_content_from_storage(self, content: bytes) -> Union[str, bytes]:
        """Process content from storage (decompression/decryption)."""
        # Decrypt if enabled
        if self.encryption_enabled:
            try:
                content = self.cipher_suite.decrypt(content)
            except Exception:
                # Content might not be encrypted
                pass
        
        # Decompress if enabled
        if self.compression_enabled:
            try:
                content = gzip.decompress(content)
            except Exception:
                # Content might not be compressed
                pass
        
        # Try to decode as UTF-8
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content

    async def _trigger_file_watchers(self, path: Path, event_type: str):
        """Trigger registered file watchers."""
        path_str = str(path)
        
        for watched_path, callbacks in self.watch_callbacks.items():
            if path_str.startswith(watched_path):
                for callback in callbacks:
                    try:
                        await callback(path_str, event_type)
                    except Exception as e:
                        logger.error(f"File watcher callback failed: {e}")

    # Transaction support
    @asynccontextmanager
    async def transaction(self, transaction_id: Optional[str] = None):
        """Context manager for atomic file operations."""
        if not transaction_id:
            transaction_id = str(uuid.uuid4())
        
        async with self.transaction_lock:
            transaction = FileTransaction(transaction_id=transaction_id)
            self.transactions[transaction_id] = transaction
            
            try:
                yield transaction
                await self._commit_transaction(transaction_id)
            except Exception as e:
                await self._rollback_transaction(transaction_id)
                raise
            finally:
                if transaction_id in self.transactions:
                    del self.transactions[transaction_id]

    async def _commit_transaction(self, transaction_id: str):
        """Commit a transaction."""
        if transaction_id not in self.transactions:
            raise ValueError(f"Transaction not found: {transaction_id}")
        
        transaction = self.transactions[transaction_id]
        transaction.committed = True
        
        logger.debug(f"Committed transaction: {transaction_id}")

    async def _rollback_transaction(self, transaction_id: str):
        """Rollback a transaction."""
        if transaction_id not in self.transactions:
            return
        
        transaction = self.transactions[transaction_id]
        
        # Execute rollback operations in reverse order
        for rollback_op in reversed(transaction.rollback_data):
            try:
                if rollback_op['operation'] == 'restore_file':
                    shutil.copy2(rollback_op['backup_path'], rollback_op['original_path'])
                elif rollback_op['operation'] == 'delete_file':
                    Path(rollback_op['path']).unlink(missing_ok=True)
            except Exception as e:
                logger.error(f"Rollback operation failed: {e}")
        
        transaction.rolled_back = True
        logger.debug(f"Rolled back transaction: {transaction_id}")

    # Bulk operations
    async def bulk_create_files(self, files: List[Dict[str, Any]], **kwargs) -> List[bool]:
        """Create multiple files in a single operation."""
        results = []
        
        async with self.transaction() as transaction:
            for file_data in files:
                try:
                    path = file_data['path']
                    content = file_data['content']
                    permissions = file_data.get('permissions')
                    
                    success = await self.create_file(path, content, permissions, **kwargs)
                    results.append(success)
                    
                except Exception as e:
                    results.append(False)
                    logger.error(f"Bulk create failed for {file_data.get('path', 'unknown')}: {e}")
        
        return results

    # File watching
    def watch_directory(self, path: Union[str, Path], callback):
        """Register a callback for file system events in a directory."""
        validated_path = str(self._validate_path(path))
        self.watch_callbacks[validated_path].append(callback)
        
        logger.debug(f"Registered watcher for: {validated_path}")

    def unwatch_directory(self, path: Union[str, Path], callback=None):
        """Unregister file system watchers."""
        validated_path = str(self._validate_path(path))
        
        if callback:
            if validated_path in self.watch_callbacks:
                try:
                    self.watch_callbacks[validated_path].remove(callback)
                except ValueError:
                    pass
        else:
            # Remove all callbacks for this path
            self.watch_callbacks.pop(validated_path, None)
        
        logger.debug(f"Unregistered watcher for: {validated_path}")

    # Resource monitoring
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        total_files = 0
        total_size = 0
        
        try:
            for item in self.base_path.rglob('*'):
                if item.is_file():
                    total_files += 1
                    total_size += item.stat().st_size
        except Exception as e:
            logger.error(f"Failed to calculate resource usage: {e}")
        
        # Get system resources
        disk_usage = psutil.disk_usage(str(self.base_path))
        memory_usage = psutil.virtual_memory()
        
        return {
            'files': {
                'count': total_files,
                'size_bytes': total_size,
                'size_mb': total_size / (1024 * 1024),
                'limit_files': self.sandbox_config.max_files,
                'limit_size_mb': self.sandbox_config.max_total_size / (1024 * 1024)
            },
            'disk': {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': disk_usage.percent
            },
            'memory': {
                'total': memory_usage.total,
                'available': memory_usage.available,
                'percent': memory_usage.percent
            }
        }

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        recent_entries = list(self.audit_log)[-limit:]
        
        return [
            {
                'timestamp': entry.timestamp.isoformat(),
                'operation': entry.operation.value,
                'path': entry.path,
                'user_id': entry.user_id,
                'success': entry.success,
                'error_message': entry.error_message,
                'metadata': entry.metadata
            }
            for entry in recent_entries
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get file system operation statistics."""
        return {
            'total_operations': self.stats.total_operations,
            'successful_operations': self.stats.successful_operations,
            'failed_operations': self.stats.failed_operations,
            'success_rate': (self.stats.successful_operations / self.stats.total_operations 
                           if self.stats.total_operations > 0 else 0),
            'bytes_read': self.stats.bytes_read,
            'bytes_written': self.stats.bytes_written,
            'files_created': self.stats.files_created,
            'files_deleted': self.stats.files_deleted,
            'security_violations': self.stats.security_violations,
            'last_operation': self.stats.last_operation.isoformat() if self.stats.last_operation else None
        }

    async def cleanup_old_backups(self, max_age_days: int = 7) -> int:
        """Clean up old backup files."""
        backup_dir = self.base_path / "backups"
        if not backup_dir.exists():
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0
        
        for backup_file in backup_dir.glob('*'):
            if backup_file.is_file():
                file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
        
        logger.info(f"Cleaned up {removed_count} old backup files")
        return removed_count

    async def validate_integrity(self) -> Dict[str, Any]:
        """Validate file system integrity."""
        issues = []
        checked_files = 0
        
        try:
            for file_path in self.base_path.rglob('*'):
                if file_path.is_file():
                    checked_files += 1
                    
                    # Check file accessibility
                    try:
                        file_path.stat()
                    except (OSError, PermissionError) as e:
                        issues.append(f"Cannot access {file_path}: {e}")
                    
                    # Check for suspicious filenames
                    try:
                        self._validate_filename(file_path.name)
                    except ValueError as e:
                        issues.append(f"Suspicious filename {file_path}: {e}")
        
        except Exception as e:
            issues.append(f"Integrity check failed: {e}")
        
        return {
            'checked_files': checked_files,
            'issues_found': len(issues),
            'issues': issues,
            'healthy': len(issues) == 0
        }