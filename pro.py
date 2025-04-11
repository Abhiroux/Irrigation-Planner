import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import json


class IrrigationPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Farm Irrigation Planner")
        self.root.geometry("1100x800")

        self.G = nx.Graph()
        self.positions = {}
        self.node_counter = 1
        self.node_types = {}

        self.selected_nodes = []

        self.setup_gui()
        self.draw_graph()

    def setup_gui(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=10)

        ttk.Button(toolbar, text="Add Plot Node",
                   command=self.add_plot_node).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Add Tank", command=self.add_tank_node).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Connect Automatically",
                   command=self.connect_nodes_auto).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Custom Connect",
                   command=self.custom_connect_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Show Kruskal MST",
                   command=self.animate_kruskal).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Dijkstra from Tank",
                   command=self.animate_dijkstra).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Save Graph",
                   command=self.save_graph).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Load Graph",
                   command=self.load_graph).pack(side=tk.LEFT, padx=5)
        # Add this line to the setup_gui() function (under other buttons)
        ttk.Button(toolbar, text="Clear Canvas",
                   command=self.clear_canvas).pack(side=tk.LEFT, padx=5)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_canvas_click)

    def add_plot_node(self):
        crop_type = simpledialog.askstring(
            "Crop Type", "Enter crop type (e.g., Rice, Wheat):")
        if not crop_type:
            return
        name = f"Plot{self.node_counter}"
        self.node_counter += 1
        self.G.add_node(name)
        self.positions[name] = (self.node_counter * 1.5, self.node_counter)
        self.node_types[name] = crop_type
        self.draw_graph()

    def add_tank_node(self):
        name = "Tank"
        if name not in self.G:
            self.G.add_node(name)
            self.positions[name] = (0, 0)
            self.node_types[name] = "Tank"
            self.draw_graph()

    def on_canvas_click(self, event):
        if event.inaxes is None:
            return

        if hasattr(self, "custom_mode") and self.custom_mode:
            node_clicked = self.find_nearest_node(event.xdata, event.ydata)
            if node_clicked:
                self.selected_nodes.append(node_clicked)
                if len(self.selected_nodes) == 2:
                    self.connect_selected_nodes()
            return

        crop_type = simpledialog.askstring(
            "Crop Type", "Enter crop type (e.g., Rice, Wheat):")
        if not crop_type:
            return
        name = f"Plot{self.node_counter}"
        self.node_counter += 1
        self.G.add_node(name)
        self.positions[name] = (event.xdata, event.ydata)
        self.node_types[name] = crop_type
        self.draw_graph()

    def find_nearest_node(self, x, y):
        for node, pos in self.positions.items():
            dist = ((pos[0] - x)**2 + (pos[1] - y)**2) ** 0.5
            if dist < 1.5:  # try increasing this if clicks aren't registering
                return node
        return None

    def custom_connect_mode(self):
        self.custom_mode = True
        self.selected_nodes = []
        messagebox.showinfo(
            "Custom Connect", "Click on two nodes to connect them manually.")

    def connect_selected_nodes(self):
        a, b = self.selected_nodes
        weight = simpledialog.askinteger(
            "Edge Weight", f"Enter weight for edge {a} - {b}:", minvalue=1)
        if weight:
            self.G.add_edge(a, b, weight=weight)
        self.selected_nodes = []
        self.custom_mode = False
        self.draw_graph()

    def connect_nodes_auto(self):
        nodes = list(self.G.nodes)
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                a, b = nodes[i], nodes[j]
                dist = ((self.positions[a][0] - self.positions[b][0]) ** 2 +
                        (self.positions[a][1] - self.positions[b][1]) ** 2) ** 0.5
                weight = max(1, int(dist) + random.randint(0, 5))
                self.G.add_edge(a, b, weight=weight)
        self.draw_graph()

    def animate_kruskal(self):
        self.ax.clear()
        mst = nx.minimum_spanning_tree(self.G, algorithm="kruskal")
        steps = list(mst.edges())
        for i in range(len(steps)):
            self.draw_graph(
                highlight_edges=steps[:i+1], color='green', title="Kruskal MST (Animating)")
            self.root.update()
            self.root.after(500)

    def animate_dijkstra(self):
        if "Tank" not in self.G:
            messagebox.showerror(
                "Error", "Tank node not found. Please add it first.")
            return

        targets = [node for node in self.G.nodes if node !=
                   "Tank" and nx.has_path(self.G, "Tank", node)]
        if not targets:
            messagebox.showinfo("Info", "No reachable plots from Tank.")
            return

        target = simpledialog.askstring(
            "Dijkstra Path", f"Enter destination node from: {', '.join(targets)}")
        if target not in self.G or target == "Tank":
            messagebox.showerror(
                "Invalid Node", "Selected node is not valid or is the Tank itself.")
            return

        path = nx.dijkstra_path(self.G, "Tank", target)
        for i in range(1, len(path)):
            self.draw_graph(highlight_edges=[(path[j], path[j+1]) for j in range(i)], color='red',
                            title=f"Dijkstra: Tank to {target} Step {i}/{len(path)-1}")
            self.root.update()
            self.root.after(500)

    def draw_graph(self, highlight_edges=None, color='blue', title="Irrigation Network"):
        self.ax.clear()
        colors = []
        for node in self.G.nodes:
            if self.node_types.get(node) == "Tank":
                colors.append('skyblue')
            elif self.node_types.get(node).lower() == "rice":
                colors.append('green')
            elif self.node_types.get(node).lower() == "wheat":
                colors.append('gold')
            else:
                colors.append('lightgray')

        labels = {}
        for node in self.G.nodes:
            crop = self.node_types.get(node, "")
            if crop == "Tank":
                labels[node] = node
            else:
                labels[node] = f"{node}\n({crop})"

        nx.draw(self.G, self.positions, ax=self.ax, labels=labels,
                node_color=colors, node_size=1000, font_weight='bold')

        edge_labels = nx.get_edge_attributes(self.G, 'weight')
        nx.draw_networkx_edge_labels(
            self.G, self.positions, edge_labels=edge_labels, ax=self.ax)

        if highlight_edges:
            nx.draw_networkx_edges(
                self.G, self.positions, edgelist=highlight_edges, width=3, edge_color=color, ax=self.ax)

        self.ax.set_title(title)
        self.canvas.draw()

    def save_graph(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        data = {
            'positions': self.positions,
            'edges': [(u, v, self.G[u][v]['weight']) for u, v in self.G.edges],
            'node_types': self.node_types
        }
        with open(file_path, 'w') as f:
            json.dump(data, f)

    def load_graph(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        with open(file_path, 'r') as f:
            data = json.load(f)
        self.G.clear()
        self.positions.clear()
        self.node_types.clear()
        for node, pos in data['positions'].items():
            self.G.add_node(node)
            self.positions[node] = tuple(pos)
        for u, v, w in data['edges']:
            self.G.add_edge(u, v, weight=w)
        self.node_types = data['node_types']
        self.draw_graph()

    def clear_canvas(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the entire canvas?"):
            self.G.clear()
            self.positions.clear()
            self.node_types.clear()
            self.node_counter = 1
            self.selected_nodes = []
            self.draw_graph()


if __name__ == '__main__':
    root = tk.Tk()
    app = IrrigationPlanner(root)
    root.mainloop()
