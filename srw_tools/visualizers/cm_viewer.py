"""Example visualizer placed under the new visualizers package.

It registers a tiny visualizer called 'square' so tests can confirm
auto-loading works.
"""
from ..visualizer import Visualizer, register_visualizer
from ..simulation_scripts import script_manager


@register_visualizer
class CoherentModeVisualizer(Visualizer):
    name = 'coherent_mode_viewer'
    group = 'Coherent Modes'

    def local_process(self, data=None):
        # produce a simple numeric grid rather than requiring external deps
        if data is None:
            return False
        
        simulation = data.get('simulation', None)
        if not simulation:
            return False
        
        # Get the CM filename from the simulation script
        script_data = script_manager.load_script(simulation)
        
        # TODO: Load the CMs from this h5 file
        # Placeholder return until implementation is complete
        return {'grid': [[0]]}
        

    def parameters(self):
        return [
            {'name': 'simulation', 'type': 'simulation', 'default': '', 'label': 'Simulation'},
            {'name': 'break1', 'type': 'newline', 'label': ''},
            {'name': 'Base CM index', 'type': 'int', 'default': 0, 'label': 'Base CM index'},
            {'name': 'break2', 'type': 'newline', 'label': ''},
            {'name': 'Number of CMs', 'type': 'int', 'default': 1, 'label': 'Number of CMs'},
        ]

    def view(self, data=None):
        """Display the grid as an image when running in a GUI."""
        output = self.process(data)

        # Use the MatplotlibEmbed helper for consistent embedding
        try:
            from ..gui_helpers import MatplotlibEmbed
            import tkinter as tk
        except Exception:
            return output

        def draw(ax):
            ax.imshow(output['grid'], cmap='gray')
            ax.set_title(self.name)

        win = tk.Toplevel()
        win.title(self.name)

        # Create a frame to hold the plot
        frame = tk.Frame(win)
        frame.pack(fill='both', expand=True)

        emb = MatplotlibEmbed(parent=frame, figsize=(4, 4))
        emb.create_figure(draw)
        return True
