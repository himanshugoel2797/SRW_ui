"""Example visualizer that supports runner selection for command execution.

This demonstrates how a visualizer can use runners to execute shell commands
and perform file operations in different environments (local or remote).
"""
from ..visualizer import Visualizer, register_visualizer
import tkinter as tk
import json


@register_visualizer
class ComputeVisualizer(Visualizer):
    """Example visualizer that uses runners to execute commands."""
    
    name = 'compute_example'
    display_name = 'Compute Example (with Runners)'
    group = 'Examples'
    description = 'Example of using runners for command execution'
    
    def supports_runners(self) -> bool:
        """Enable runner selection for this visualizer."""
        return True
    
    def local_process(self, data=None):
        """Perform computation using the runner if available.
        
        This demonstrates executing a Python command via the runner system.
        """
        n = (data or {}).get('size', 10)
        
        if self.runner:
            # Use runner to execute a command
            python_cmd = f"python -c \"import json; result = [i*i for i in range({n})]; print(json.dumps({{'values': result, 'count': len(result)}}))\""
            
            try:
                exit_code, stdout, stderr = self.runner.run_command(python_cmd)
                
                if exit_code == 0:
                    try:
                        result = json.loads(stdout)
                        result['executed_via'] = self.runner.get_display_name()
                        result['runner_type'] = self.runner.name
                        return result
                    except json.JSONDecodeError:
                        return {'error': 'Failed to parse command output', 'raw': stdout}
                else:
                    return {'error': stderr or 'Command failed', 'exit_code': exit_code}
            except Exception as e:
                return {'error': str(e)}
        else:
            # Fallback to local computation without runner
            result = [i * i for i in range(n)]
            return {'values': result, 'count': len(result), 'executed_via': 'Direct (no runner)'}
    
    def parameters(self):
        """Define input parameters for this visualizer."""
        return [
            {'name': 'size', 'type': 'int', 'default': 10, 'label': 'Number of values'},
        ]
    
    def view(self, data=None):
        """Display the computation results with a runner selector.

        Uses the shared `create_runner_selector` helper so users can pick a
        runner instance to execute the computation via the runner system.
        """
        win = tk.Toplevel()
        win.title(self.display_name)

        frame = tk.Frame(win, padx=20, pady=20)
        frame.pack(fill='both', expand=True)

        # Runner selector helper (lazy import to avoid hard dependency when
        # used in non-GUI contexts).
        try:
            from ..runner_selector import create_runner_selector
            selector_widget, get_runner_fn = create_runner_selector(frame, initial_instance=None)
            if selector_widget is not None:
                selector_widget.pack(anchor='w', pady=(0, 10))
        except Exception:
            get_runner_fn = lambda: None

        # Area where results will be displayed (so re-run can update it)
        results_container = tk.Frame(frame)
        results_container.pack(fill='both', expand=True)

        def render_output(output):
            for child in results_container.winfo_children():
                child.destroy()

            if not output:
                tk.Label(results_container, text='No output', fg='gray').pack(anchor='w')
                return

            if 'error' in output:
                tk.Label(results_container, text=f"Error: {output['error']}", fg='red').pack(anchor='w')
                if 'raw' in output:
                    tk.Label(results_container, text=f"Raw output: {output['raw'][:200]}...", fg='gray').pack(anchor='w', pady=(5, 0))
            else:
                tk.Label(results_container, text=f"Computed {output.get('count', 0)} values:").pack(anchor='w')
                values = output.get('values', [])
                display_vals = values[:10]
                more_text = f" (showing first 10 of {len(values)})" if len(values) > 10 else ""
                tk.Label(results_container, text=str(display_vals) + more_text).pack(anchor='w', pady=(5, 0))

            exec_info = output.get('executed_via', 'Unknown')
            runner_type = output.get('runner_type', '')
            info_text = f"Executed via: {exec_info}"
            if runner_type:
                info_text += f" ({runner_type})"
            tk.Label(results_container, text=info_text, fg='blue').pack(anchor='w', pady=(10, 0))

        def do_run():
            # set visualizer runner from selector and run
            try:
                self.runner = get_runner_fn()
            except Exception:
                self.runner = None

            output = self.process(data)
            render_output(output)

        # Run / Re-run button
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill='x', pady=(6, 6))
        tk.Button(btn_frame, text='Run', command=do_run, width=10).pack(side=tk.LEFT)

        # initial run
        do_run()

        return True


