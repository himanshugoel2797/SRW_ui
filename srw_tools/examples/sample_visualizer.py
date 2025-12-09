"""A tiny example visualizer showing use of the Visualizer registry.

This is intentionally minimal — it creates a simple sine curve plot if
matplotlib is available, otherwise it just returns the computed data.
"""
from ..visualizer import Visualizer, register_visualizer


@register_visualizer
class SineVisualizer(Visualizer):
    name = 'sine'

    def run(self, data=None):
        # import numpy only when needed so the module can be imported
        # even if numpy isn't installed.
        try:
            import numpy as np
        except Exception:
            np = None

        if np is None:
            # return a fallback numerical representation
            x = [0]
            y = [0]
        else:
            x = np.linspace(0, 2 * np.pi, 200)
        amp = (data or {}).get('amplitude', 1.0)
        y = amp * np.sin(x)

        # avoid importing matplotlib if consumer doesn't need plotting
        try:
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(x, y)
            plt.title(f'Sine wave (amp={amp})')
            plt.xlabel('x')
            plt.ylabel('sin(x)')
            plt.close()
        except Exception:
            # return the numerical data as fallback
                return {'x': x.tolist() if hasattr(x, 'tolist') else list(x),
                    'y': y.tolist() if hasattr(y, 'tolist') else list(y)}

        return True
