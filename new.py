import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random


class IrrigationPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Farm Irrigation Planner")
        self.root.geometry("1100x800")

        self.G = nx.Graph()
        self.positions = {}
        self.node_counter = 1

        self.setup_gui()
        self.draw_graph()

    def setup_gui(self):
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=10)

        ttk.Button(toolbar, text="Add Plot Node",
                   command=self.add_plot_node).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Add Tank", command=self.add_tank_node).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Connect Nodes",
                   command=self.connect_nodes).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Show Kruskal MST",
                   command=self.show_kruskal_mst).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Dijkstra from Tank",
                   command=self.show_dijkstra).pack(side=tk.LEFT, padx=5)

        # Graph canvas
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_canvas_click)

    def add_plot_node(self):
        name = f"Plot{self.node_counter}"
        self.node_counter += 1
        self.G.add_node(name)
        self.positions[name] = (self.node_counter * 1.5, self.node_counter)
        self.draw_graph()

    def add_tank_node(self):
        name = "Tank"
        if name not in self.G:
            self.G.add_node(name)
            self.positions[name] = (0, 0)
            self.draw_graph()

    def on_canvas_click(self, event):
        if event.inaxes is None:
            return
        name = f"Plot{self.node_counter}"
        self.node_counter += 1
        self.G.add_node(name)
        self.positions[name] = (event.xdata, event.ydata)
        self.draw_graph()

    def connect_nodes(self):
        nodes = list(self.G.nodes)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, b = nodes[i], nodes[j]
                dist = ((self.positions[a][0] - self.positions[b][0]) ** 2 +
                        (self.positions[a][1] - self.positions[b][1]) ** 2) ** 0.5
                weight = max(1, int(dist) + random.randint(0, 5))
                self.G.add_edge(a, b, weight=weight)
        self.draw_graph()

    def show_kruskal_mst(self):
        mst = nx.minimum_spanning_tree(self.G, algorithm="kruskal")
        self.draw_graph(highlight_edges=mst.edges(),
                        color='green', title="Kruskal MST")

    def show_dijkstra(self):
        if "Tank" not in self.G:
            messagebox.showerror(
                "Error", "Tank node not found. Please add it first.")
            return

        targets = [node for node in self.G.nodes if node !=
                   "Tank" and nx.has_path(self.G, "Tank", node)]
        if not targets:
            messagebox.showinfo("Info", "No reachable plots from Tank.")
            return

        # Ask user for destination node
        target = simpledialog.askstring(
            "Dijkstra Path", f"Enter destination node from: {', '.join(targets)}")
        if target not in self.G or target == "Tank":
            messagebox.showerror(
                "Invalid Node", "Selected node is not valid or is the Tank itself.")
            return

        path = nx.dijkstra_path(self.G, "Tank", target)
        path_edges = list(zip(path, path[1:]))
        total_weight = sum(self.G[u][v]['weight'] for u, v in path_edges)
        self.draw_graph(highlight_edges=path_edges, color='red',
                        title=f"Dijkstra: Tank to {target} (Cost: {total_weight})")

    def draw_graph(self, highlight_edges=None, color='blue', title="Irrigation Network"):
        self.ax.clear()
        nx.draw(self.G, self.positions, ax=self.ax, with_labels=True,
                node_color='lightblue', node_size=1000, font_weight='bold')
        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(
            self.G, self.positions, edge_labels=edge_labels, ax=self.ax)

        if highlight_edges:
            nx.draw_networkx_edges(
                self.G, self.positions, edgelist=highlight_edges, width=3, edge_color=color, ax=self.ax)

        self.ax.set_title(title)
        self.canvas.draw()


if __name__ == '__main__':
    root = tk.Tk()
    app = IrrigationPlanner(root)
    root.mainloop()
