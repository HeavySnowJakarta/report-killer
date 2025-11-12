"""Code execution utilities for the agent."""

import subprocess
import os
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console

console = Console()


class CodeExecutor:
    """Handles code compilation and execution."""
    
    def __init__(self, workspace_dir: str = "workspace"):
        """Initialize the code executor with a workspace directory."""
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)
        self.system = platform.system()
        
        # Track available tools
        self.available_tools = self._detect_tools()
    
    def _detect_tools(self) -> Dict[str, bool]:
        """Detect available compilation and execution tools."""
        tools = {}
        
        # C/C++ compilers
        tools['gcc'] = shutil.which('gcc') is not None
        tools['g++'] = shutil.which('g++') is not None
        tools['cl'] = shutil.which('cl') is not None  # MSVC
        tools['clang'] = shutil.which('clang') is not None
        
        # Python
        tools['python'] = shutil.which('python') is not None or shutil.which('python3') is not None
        
        # Java
        tools['javac'] = shutil.which('javac') is not None
        tools['java'] = shutil.which('java') is not None
        
        # Other
        tools['node'] = shutil.which('node') is not None
        tools['go'] = shutil.which('go') is not None
        
        return tools
    
    def get_available_languages(self) -> List[str]:
        """Get list of languages that can be executed."""
        languages = []
        
        if self.available_tools.get('gcc') or self.available_tools.get('g++'):
            languages.append('C')
            languages.append('C++')
        
        if self.available_tools.get('python'):
            languages.append('Python')
        
        if self.available_tools.get('javac') and self.available_tools.get('java'):
            languages.append('Java')
        
        if self.available_tools.get('node'):
            languages.append('JavaScript')
        
        if self.available_tools.get('go'):
            languages.append('Go')
        
        return languages
    
    def can_execute_language(self, language: str) -> Tuple[bool, str]:
        """Check if a specific language can be executed."""
        language = language.lower()
        
        if language in ['c', 'c++', 'cpp']:
            if self.available_tools.get('gcc') or self.available_tools.get('g++'):
                return True, "gcc/g++ available"
            else:
                return False, "No C/C++ compiler found. Please install gcc/g++ or Visual Studio."
        
        elif language == 'python':
            if self.available_tools.get('python'):
                return True, "Python available"
            else:
                return False, "Python not found. Please install Python 3."
        
        elif language == 'java':
            if self.available_tools.get('javac') and self.available_tools.get('java'):
                return True, "Java available"
            else:
                return False, "Java not found. Please install JDK."
        
        else:
            return False, f"Language {language} not supported"
    
    def write_code(self, filename: str, code: str) -> Path:
        """Write code to a file in the workspace."""
        filepath = self.workspace / filename
        filepath.write_text(code, encoding='utf-8')
        return filepath
    
    def compile_c_cpp(self, source_file: Path, output_file: Optional[Path] = None) -> Tuple[bool, str]:
        """Compile C/C++ code."""
        if output_file is None:
            output_file = source_file.with_suffix('.exe' if self.system == 'Windows' else '')
        
        # Determine compiler
        if source_file.suffix in ['.cpp', '.cc', '.cxx']:
            compiler = 'g++' if self.available_tools.get('g++') else 'gcc'
        else:
            compiler = 'gcc' if self.available_tools.get('gcc') else 'g++'
        
        try:
            result = subprocess.run(
                [compiler, str(source_file), '-o', str(output_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.workspace
            )
            
            if result.returncode == 0:
                return True, f"Compiled successfully to {output_file.name}"
            else:
                return False, f"Compilation error:\n{result.stderr}"
        
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, f"Compilation error: {e}"
    
    def run_executable(self, executable: Path, args: List[str] = None, input_data: str = None) -> Tuple[bool, str]:
        """Run a compiled executable."""
        if args is None:
            args = []
        
        try:
            result = subprocess.run(
                [str(executable)] + args,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=30,
                cwd=self.workspace
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr:\n{result.stderr}"
            
            return result.returncode == 0, output
        
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (30s limit)"
        except Exception as e:
            return False, f"Execution error: {e}"
    
    def run_python(self, script_file: Path, args: List[str] = None, input_data: str = None) -> Tuple[bool, str]:
        """Run a Python script."""
        python_cmd = 'python3' if shutil.which('python3') else 'python'
        
        if args is None:
            args = []
        
        try:
            result = subprocess.run(
                [python_cmd, str(script_file)] + args,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=30,
                cwd=self.workspace
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nStderr:\n{result.stderr}"
            
            return result.returncode == 0, output
        
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (30s limit)"
        except Exception as e:
            return False, f"Execution error: {e}"
    
    def execute_code(self, language: str, code: str, filename: str = None, 
                     input_data: str = None) -> Tuple[bool, str, Optional[Path]]:
        """
        Execute code in the specified language.
        
        Returns:
            (success, output, code_file_path)
        """
        language = language.lower()
        
        # Check if language can be executed
        can_execute, message = self.can_execute_language(language)
        if not can_execute:
            return False, message, None
        
        # Determine filename
        if filename is None:
            if language in ['c']:
                filename = 'code.c'
            elif language in ['c++', 'cpp']:
                filename = 'code.cpp'
            elif language == 'python':
                filename = 'code.py'
            elif language == 'java':
                filename = 'Code.java'
            else:
                filename = 'code.txt'
        
        # Write code to file
        code_file = self.write_code(filename, code)
        
        # Execute based on language
        if language in ['c', 'c++', 'cpp']:
            # Compile
            success, compile_output = self.compile_c_cpp(code_file)
            if not success:
                return False, f"Compilation failed:\n{compile_output}", code_file
            
            # Run
            executable = code_file.with_suffix('.exe' if self.system == 'Windows' else '')
            success, run_output = self.run_executable(executable, input_data=input_data)
            
            output = f"Compilation successful.\n\nExecution output:\n{run_output}"
            return success, output, code_file
        
        elif language == 'python':
            success, output = self.run_python(code_file, input_data=input_data)
            return success, output, code_file
        
        else:
            return False, f"Execution not implemented for {language}", code_file
    
    def cleanup(self):
        """Clean up workspace directory."""
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
            self.workspace.mkdir(exist_ok=True)
