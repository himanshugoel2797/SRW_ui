"""Runner Manager Visualizer for configuring runner instances.

This visualizer provides a UI for creating, editing, and managing
named runner instances that can be used by other visualizers.
"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading

from ..visualizer import Visualizer, register_visualizer
from ..runner_registry import (
    list_runners, list_runner_instances, create_runner, 
    get_runner_instance, remove_runner_instance, save_runner_instance,
    load_runner_configs, get_runner_class
)


@register_visualizer
class RunnerManagerVisualizer(Visualizer):
    """Visualizer for managing runner instances."""
    
    name = 'runner_manager'
    display_name = 'Runner Manager'
    group = 'System'
    description = 'Configure and manage runner instances'
    
    def supports_runners(self) -> bool:
        """This visualizer doesn't need a runner itself."""
        return False
    
    def local_process(self, data=None):
        """Not applicable for this UI-only visualizer."""
        return None
    
    def view(self, data=None):
        """Display the runner management UI."""
        win = tk.Toplevel()
        win.title(self.display_name)
        win.geometry('800x600')
        
        # Main container
        main_frame = tk.Frame(win, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top section: Instance list
        list_frame = tk.LabelFrame(main_frame, text='Runner Instances', padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Listbox with scrollbar
        list_container = tk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        instance_listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set)
        instance_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=instance_listbox.yview)
        
        # Instance details
        details_frame = tk.Frame(list_frame)
        details_frame.pack(fill=tk.X, pady=(10, 0))
        
        details_label = tk.Label(details_frame, text='Select an instance to view details', 
                                fg='gray', justify=tk.LEFT, anchor='w')
        details_label.pack(fill=tk.X)
        
        def refresh_list():
            """Refresh the instance list."""
            instance_listbox.delete(0, tk.END)
            # Show configured instances (saved) as well as any in-memory instances
            saved = set(load_runner_configs().keys())
            inmem = set(list_runner_instances())
            instances = sorted(saved | inmem)
            for inst_name in instances:
                instance_listbox.insert(tk.END, inst_name)
        
        def show_instance_details(event=None):
            """Display details of selected instance."""
            selection = instance_listbox.curselection()
            if not selection:
                details_label.config(text='Select an instance to view details', fg='gray')
                return
            
            instance_name = instance_listbox.get(selection[0])
            try:
                try:
                    runner = get_runner_instance(instance_name)
                except KeyError:
                    # If instance exists in saved configs but not yet created,
                    # lazily create it now so we can inspect/test it.
                    configs = load_runner_configs()
                    config = configs.get(instance_name, {})
                    rtype = config.get('type')
                    if rtype:
                        try:
                            runner = create_runner(rtype, config, instance_name)
                        except Exception:
                            runner = None
                    else:
                        runner = None
                else:
                    configs = load_runner_configs()
                    config = configs.get(instance_name, {})
                runner_type = config.get('type', 'unknown')
                
                details = []
                details.append(f"Instance: {instance_name}")
                details.append(f"Type: {runner_type}")
                details.append(f"Status: {'Available' if runner.is_available() else 'Not Available'}")
                details.append(f"Config: {', '.join([f'{k}={v}' for k, v in config.items() if k != 'type'])}")
                
                details_label.config(text='\n'.join(details), fg='black')
            except Exception as e:
                details_label.config(text=f'Error loading instance: {e}', fg='red')
        
        instance_listbox.bind('<<ListboxSelect>>', show_instance_details)
        
        # Button panel
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def create_new_instance():
            """Create a new runner instance."""
            # Select runner type
            type_win = tk.Toplevel(win)
            type_win.title('Select Runner Type')
            type_win.geometry('400x300')
            
            frame = tk.Frame(type_win, padx=20, pady=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            tk.Label(frame, text='Select Runner Type:', font=('', 12, 'bold')).pack(anchor='w', pady=(0, 10))
            
            runner_types = list_runners()
            selected_type = tk.StringVar()
            
            for runner_type in runner_types:
                try:
                    cls = get_runner_class(runner_type)
                    desc = getattr(cls, 'description', runner_type)
                    display = getattr(cls, 'display_name', runner_type)
                    
                    rb = tk.Radiobutton(frame, text=f"{display}", 
                                       variable=selected_type, value=runner_type)
                    rb.pack(anchor='w', pady=2)
                    
                    tk.Label(frame, text=f"  {desc}", fg='gray', font=('', 9)).pack(anchor='w', padx=(20, 0))
                except Exception:
                    pass
            
            if runner_types:
                selected_type.set(runner_types[0])
            
            def proceed():
                runner_type = selected_type.get()
                if not runner_type:
                    messagebox.showwarning('No selection', 'Please select a runner type')
                    return
                
                type_win.destroy()
                configure_instance(runner_type)
            
            tk.Button(frame, text='Next', command=proceed, width=10).pack(pady=(20, 0))
            tk.Button(frame, text='Cancel', command=type_win.destroy, width=10).pack(pady=(5, 0))
        
        def configure_instance(runner_type, existing_name=None):
            """Configure a runner instance."""
            config_win = tk.Toplevel(win)
            config_win.title(f'Configure {runner_type} Runner')
            config_win.geometry('500x400')
            
            frame = tk.Frame(config_win, padx=20, pady=20)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Instance name
            tk.Label(frame, text='Instance Name:', font=('', 10, 'bold')).pack(anchor='w')
            name_entry = tk.Entry(frame, width=40)
            name_entry.pack(fill=tk.X, pady=(5, 15))
            
            if existing_name:
                name_entry.insert(0, existing_name)
                name_entry.config(state='readonly')
            
            # Get schema for this runner type
            try:
                cls = get_runner_class(runner_type)
                temp_runner = cls({})
                schema = temp_runner.get_config_schema()
            except Exception:
                schema = []
            
            # Create config widgets
            from ..parameter_widgets import create_parameter_widgets, create_parameter_getter
            from .. import simulation_scripts
            
            if schema:
                tk.Label(frame, text='Configuration:', font=('', 10, 'bold')).pack(anchor='w', pady=(0, 5))
                config_frame = tk.Frame(frame)
                config_frame.pack(fill=tk.BOTH, expand=True)
                
                widgets, rows, labels = create_parameter_widgets(schema, config_frame, simulation_scripts)
                getter = create_parameter_getter(widgets)
                
                # Pre-fill if editing existing
                if existing_name:
                    try:
                        configs = load_runner_configs()
                        existing_config = configs.get(existing_name, {})
                        for param in schema:
                            param_name = param['name']
                            if param_name in existing_config and param_name in widgets:
                                widget = widgets[param_name]
                                value = existing_config[param_name]
                                if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                                    widget.delete(0, tk.END)
                                    widget.insert(0, str(value))
                    except Exception:
                        pass
            else:
                getter = lambda: {}
            
            def save():
                instance_name = name_entry.get().strip()
                if not instance_name:
                    messagebox.showwarning('Invalid name', 'Please enter an instance name')
                    return
                
                config = getter()
                
                try:
                    save_runner_instance(instance_name, runner_type, config)
                    messagebox.showinfo('Success', f'Runner instance "{instance_name}" saved')
                    config_win.destroy()
                    refresh_list()
                except Exception as e:
                    messagebox.showerror('Error', f'Failed to save instance: {e}')
            
            btn_frame = tk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=(20, 0))
            
            tk.Button(btn_frame, text='Save', command=save, width=10).pack(side=tk.LEFT, padx=(0, 5))
            tk.Button(btn_frame, text='Cancel', command=config_win.destroy, width=10).pack(side=tk.LEFT)
        
        def edit_instance():
            """Edit selected instance."""
            selection = instance_listbox.curselection()
            if not selection:
                messagebox.showwarning('No selection', 'Please select an instance to edit')
                return
            
            instance_name = instance_listbox.get(selection[0])
            try:
                configs = load_runner_configs()
                config = configs.get(instance_name, {})
                runner_type = config.get('type')
                
                if not runner_type:
                    messagebox.showerror('Error', 'Cannot determine runner type')
                    return
                
                configure_instance(runner_type, instance_name)
            except Exception as e:
                messagebox.showerror('Error', f'Failed to load instance: {e}')
        
        def delete_instance():
            """Delete selected instance."""
            selection = instance_listbox.curselection()
            if not selection:
                messagebox.showwarning('No selection', 'Please select an instance to delete')
                return
            
            instance_name = instance_listbox.get(selection[0])
            
            if not messagebox.askyesno('Confirm Delete', 
                                      f'Delete runner instance "{instance_name}"?'):
                return
            
            try:
                # Try to remove in-memory instance if present
                try:
                    remove_runner_instance(instance_name)
                except Exception:
                    pass

                # Remove from saved configs
                configs = load_runner_configs()
                if instance_name in configs:
                    del configs[instance_name]
                    from ..runner_registry import save_runner_configs
                    save_runner_configs(configs)

                refresh_list()
                details_label.config(text='Instance deleted', fg='green')
                messagebox.showinfo('Success', f'Instance "{instance_name}" deleted')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to delete instance: {e}')
        
        def test_connection():
            """Test connection for selected instance."""
            selection = instance_listbox.curselection()
            if not selection:
                messagebox.showwarning('No selection', 'Please select an instance to test')
                return
            
            instance_name = instance_listbox.get(selection[0])
            
            try:
                try:
                    runner = get_runner_instance(instance_name)
                except KeyError:
                    # lazily create instance from saved config
                    configs = load_runner_configs()
                    config = configs.get(instance_name, {})
                    rtype = config.get('type')
                    if rtype:
                        runner = create_runner(rtype, config, instance_name)
                    else:
                        raise RuntimeError('No saved configuration for instance')

                if hasattr(runner, 'connect'):
                    details_label.config(text='Connecting...', fg='blue')
                    
                    def worker():
                        ok, msg = runner.connect()
                        if ok:
                            details_label.config(text=f'Connection successful: {msg}', fg='green')
                            messagebox.showinfo('Success', msg)
                        else:
                            details_label.config(text=f'Connection failed: {msg}', fg='red')
                            messagebox.showerror('Connection Failed', msg)
                        show_instance_details()
                    
                    threading.Thread(target=worker, daemon=True).start()
                else:
                    messagebox.showinfo('Test', f'{runner.get_display_name()} is ready (no connection needed)')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to test instance: {e}')
        
        tk.Button(button_frame, text='New Instance', command=create_new_instance, width=15).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(button_frame, text='Edit', command=edit_instance, width=10).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(button_frame, text='Delete', command=delete_instance, width=10).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(button_frame, text='Test Connection', command=test_connection, width=15).pack(side=tk.LEFT, padx=(0, 5))
        
        # Initial load
        refresh_list()
        
        return True
