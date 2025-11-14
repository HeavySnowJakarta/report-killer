"""Chart and visualization generation utilities."""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional, Dict, List
import platform

# Fix Chinese font issues - use DejaVu Sans as fallback
try:
    if platform.system() == 'Windows':
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    elif platform.system() == 'Darwin':  # macOS
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Songti SC', 'DejaVu Sans']
    else:  # Linux
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display


class ChartGenerator:
    """Generate charts and visualizations for documents."""
    
    def __init__(self, workspace_dir: str = "workspace"):
        """Initialize chart generator."""
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)
        self.chart_counter = 0
    
    def generate_chart(self, code: str, output_filename: Optional[str] = None) -> Optional[str]:
        """
        Execute matplotlib code and save the chart.
        
        Args:
            code: Python code using matplotlib
            output_filename: Optional filename for the chart
        
        Returns:
            Path to the generated chart image, or None if failed
        """
        if output_filename is None:
            self.chart_counter += 1
            output_filename = f"chart_{self.chart_counter}.png"
        
        output_path = self.workspace / output_filename
        
        try:
            # Create a clean namespace with plt
            namespace = {'plt': plt, 'output_path': str(output_path)}
            
            # Add common imports
            import numpy as np
            namespace['np'] = np
            
            # Execute the code
            exec(code, namespace)
            
            # If plt.savefig wasn't called, save the current figure
            if not output_path.exists():
                plt.savefig(str(output_path), dpi=150, bbox_inches='tight')
            
            plt.close('all')  # Clean up
            
            if output_path.exists():
                return str(output_path)
            else:
                return None
                
        except Exception as e:
            print(f"Error generating chart: {e}")
            plt.close('all')
            return None
    
    def parse_chart_from_code(self, code: str) -> Optional[str]:
        """
        Parse matplotlib code from a code block and generate the chart.
        
        Looks for plt.savefig() calls or adds one if not present.
        """
        # Check if code contains matplotlib/plt usage
        if 'plt.' not in code and 'matplotlib' not in code:
            return None
        
        # If code doesn't have savefig, add it
        if 'savefig' not in code:
            code = code + f"\nplt.savefig(output_path, dpi=150, bbox_inches='tight')"
        
        return self.generate_chart(code)
