import json
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
from PIL import Image

from astar import astar
from stations_graph import data_graph


class MetroApp(ctk.CTk):
    def __init__(self):
        super().__init__()


        self.title("Metro Ciudad de México")
        self.geometry("400x750")
        ctk.set_appearance_mode("light")
        self.resizable(False, False)

        with open("metro_CDMX.json", "r") as f:
            self.data = json.load(f)
        self.graph, self.positions, self.label_pos, self.elevators, self.line_colors = data_graph(self.data)

        self.bg_photo = None
        self.canvas = None
        self.ax = None
        self.fig = None
        self.need_elev = None
        self.end_var = ctk.StringVar(value="¿Adónde quieres ir?")
        self.start_var = ctk.StringVar(value="¿Dónde estás?")
        self.time = None
        self.day = None
        self.est_time = None
        self.nchanges = None
        self.start_walk = False
        self.end_walk = False
        self.message = None

        self.display()

    def display(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.bg_photo = ctk.CTkImage(Image.open("background.png"), size=(400, 750))
        bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        header = ctk.CTkFrame(self, corner_radius=0, fg_color="white")
        header.pack(pady=50)
        ctk.CTkLabel(header, text="CDMX Metro", font=("Arial Bold", 26)).pack(pady=10)

        control_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="white")
        control_frame.pack(side="bottom", pady=62, padx=35, fill="x")

        ctk.CTkLabel(control_frame, text="¿Adónde vas?", font=("Arial Rounded MT Bold", 20)).pack(pady=20)
        stations = sorted(list(self.data["stations"].keys()))


        ctk.CTkLabel(control_frame, text="Origen", font=("Arial Rounded MT Bold", 14), anchor="w",
                     text_color="gray").pack(fill="x")
        ctk.CTkComboBox(
            control_frame, values=stations,
            height=40,
            variable=self.start_var,
            fg_color="white", font=("Arial Rounded MT Bold", 16),
            button_color="light gray", border_color="light gray"
        ).pack(pady=(0, 15), fill="x")


        ctk.CTkLabel(control_frame, text="Destino", font=("Arial Rounded MT Bold", 14), anchor="w",
                     text_color="gray").pack(fill="x")
        ctk.CTkComboBox(
            control_frame, values=stations,
            height=40,
            variable=self.end_var,
            fg_color="white", font=("Arial Rounded MT Bold", 16),
            button_color="light gray", border_color="light gray"
        ).pack(pady=(0, 15), fill="x")

        date_frame = ctk.CTkFrame(control_frame, fg_color="white")
        date_frame.pack(pady=10, fill="x")
        time_frame = ctk.CTkFrame(date_frame, fg_color="white")
        time_frame.pack(side="right", fill="both", expand=True)
        day_frame = ctk.CTkFrame(date_frame, fg_color="white")
        day_frame.pack(side="left", fill="both", expand=True)

        self.time = ctk.StringVar(value="00h")
        self.day = ctk.StringVar(value="Lunes - Viernes")
        ctk.CTkLabel(day_frame, text="Día:", font=("Arial Rounded MT Bold", 12)).pack(side="left", expand=True)
        ctk.CTkLabel(time_frame, text="Hora:", font=("Arial Rounded MT Bold", 12)).pack(side="left", expand=True)
        ctk.CTkComboBox(day_frame, values=["Lunes - Viernes", "Sábado", "Domingo y festivos"],
                        width=140, variable=self.day, font=("Arial Rounded MT Bold", 12)).pack()
        self.time = ctk.StringVar(value="08h")
        ctk.CTkComboBox(time_frame, values=[f"{h:02d}h" for h in range(24)], width=100, variable=self.time,
                        font=("Arial Rounded MT Bold", 12)).pack()

        self.need_elev = ctk.BooleanVar(value=False)
        accessibility_check = ctk.CTkCheckBox(
            control_frame,
            text="Accesible (sillas de ruedas, ascensores, etc.)",
            font=("Arial Rounded MT Bold", 12),
            variable=self.need_elev,
            onvalue=True,
            offvalue=False,
            fg_color="#FA7700",
            hover_color="#FA6300"
        )
        accessibility_check.pack(pady=10)

        ctk.CTkButton(
            control_frame, text="Buscar Ruta",
            height=40, corner_radius=20, font=("Arial Rounded MT Bold", 16),
            command=self.search, fg_color="#FA7700",
            hover_color="#FA6300", width=120,
        ).pack(pady=5, padx=20, fill="x")

        ctk.CTkButton(
            control_frame, text="Ver Mapa",
            height=30, corner_radius=20, font=("Arial Rounded MT Bold", 16),
            command=self.display_map, fg_color="#575757",
            hover_color="#303030", width=60,
        ).pack(pady=5, padx=20)

    def display_map(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.bg_photo = ctk.CTkImage(Image.open("background.png"), size=(400, 750))
        bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        button_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        button_frame.pack(pady=62)

        ctk.CTkButton(
            button_frame, text="Volver", text_color="black",
            command=self.display, fg_color="white", font=("Arial Rounded MT Bold", 16),
            hover_color="light gray", width=120,
        ).pack(padx=10)

        map_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="white")
        map_frame.pack(side="bottom", pady=150, padx=35, fill="x")

        self.fig, self.ax = plt.subplots()
        self.fig.tight_layout(pad=0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.map()

    def count_changes(self, path):
        path_edges = list(zip(path[:-1], path[1:]))
        line = self.graph[path[0]][path[1]]["line"]
        res = 0
        steps = []
        if self.start_walk:
            steps.append(f"La estación {self.start_var.get()} no es accesible. Se debe caminar hasta la estación {path[0]}")
        steps.append(f"Toma la línea {line} desde {path[0]} en dirección a {path[1]}.")
        for edge in path_edges:
            cur_line = self.graph[edge[0]][edge[1]]["line"]
            if cur_line != line:
                steps.append(f"Viaja en la línea {line} hasta la estación {edge[0]}.")
                steps.append(f"En la estación {edge[0]}, cambie a la línea {cur_line} en dirección a {edge[1]}.")
                line = cur_line
                res += 1
        steps.append(f"Bájese en la estación {path[-1]}")
        if self.end_walk:
            steps.append(f"Se debe caminar hasta la estación {self.end_var.get()}")
        return res, steps

    def display_path(self, path):
        for widget in self.winfo_children():
            widget.destroy()

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame, text="Volver", command=self.display,
            fg_color="#555555", hover_color="#777777",
            width=120, height=35, font=("Arial Rounded MT Bold", 14)
        ).pack(padx=10)

        if len(path) < 2:
            ctk.CTkLabel(button_frame, text=self.message,
                         font=("Arial Rounded MT Bold", 24), text_color="black").pack(side="top", pady=100)

        else:

            map_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="white")
            map_frame.pack(padx=20, pady=10, fill="both", expand=True)

            self.fig, self.ax = plt.subplots()
            self.fig.tight_layout(pad=0)
            self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
            self.canvas.get_tk_widget().pack(fill="both", padx=10, pady=10)

            self.map(path)

            info_frame = ctk.CTkFrame(self, fg_color="transparent")
            info_frame.pack(pady=10, padx=20, fill="x")

            boxes_row = ctk.CTkFrame(info_frame, fg_color="transparent")
            boxes_row.pack(fill="x", padx=10)

            def create_info_box(parent, title, value):
                box = ctk.CTkFrame(parent, corner_radius=15, fg_color="#d9d9d9")
                box.pack(side="left", expand=True, fill="both", padx=10, pady=5)

                ctk.CTkLabel(box, text=title, font=("Arial Rounded MT Bold", 12), text_color="#333333").pack(
                    pady=(10, 2))
                ctk.CTkLabel(box, text=value, font=("Arial Rounded MT Bold", 14), text_color="#000000").pack(
                    pady=(0, 10))

            nstations = len(path) - 1
            self.nchanges, steps = self.count_changes(path)

            create_info_box(boxes_row, "Tiempo Estimado", f"{self.est_time} min")
            create_info_box(boxes_row, "Estaciones", nstations)
            create_info_box(boxes_row, "Cambios", self.nchanges)

            scroll_frame = ctk.CTkScrollableFrame(self, label_text="Etapas del viaje",
                                                  label_font=("Arial Rounded MT Bold", 18))
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
            for i in steps:
                ctk.CTkLabel(scroll_frame, text=i,
                             font=("Arial Rounded MT Bold", 14),
                             anchor="w", wraplength=300, justify="left",
                             ).pack(pady=5, anchor="w", padx=10)

    def map(self, path=None):
        self.ax.clear()

        nx.draw_networkx_nodes(self.graph, self.positions, node_size=100,
                               node_color="white", edgecolors="black")
        nx.draw_networkx_labels(self.graph, self.label_pos, font_size=8, font_color="black", horizontalalignment="left")

        light = {"#c23c7f": "#ff9fcf", "#8d8926": "#d3d085", "#e58126": "#f6c292", "#774234": "#b8988f",
                 "#a88c39": "#e2d098"}

        for color, edges in self.line_colors.items():
            edge_col = light[color] if path else color
            width = 4 if path else 10
            nx.draw_networkx_edges(self.graph, self.positions, edgelist=edges, edge_color=edge_col, width=width)

        if path:
            rednodes = [self.start_var.get(), self.end_var.get()]
            nx.draw_networkx_nodes(self.graph, self.positions, nodelist=rednodes, node_size=100,
                                   node_color="red", edgecolors="black")
            path_edges = list(zip(path[:-1], path[1:]))
            for color, edges in self.line_colors.items():
                path_on_line = [e for e in path_edges if e in edges or (e[::-1] in edges)]
                if path_on_line:
                    nx.draw_networkx_edges(self.graph, self.positions, edgelist=path_on_line, edge_color=color, width=8)

        self.ax.set_axis_off()
        self.canvas.draw()

    def search(self):

        start = self.start_var.get()
        end = self.end_var.get()

        if not (start == "¿Dónde estás?" or end == "¿Adónde quieres ir?") and start != end:
            time = self.time.get()
            day = self.day.get()

            if ((0 <= int(time[:2]) < 5 and day == "Lunes - Viernes")
                    or (1 <= int(time[:2]) < 6 and day == "Sábado")
                    or (1 <= int(time[:2]) < 7 and day == "Domingo y festivos")):
                self.message = "Lo sentimos,\npero el metro esta\nactualmente cerrado."
                self.display_path([])

            else:
                if self.need_elev.get():

                    def closest_elevator(node):
                        res = None
                        dist = 10
                        for neighbor, info in self.graph[node].items():
                            if self.elevators[neighbor] and info["weight"] < dist:
                                res = neighbor
                        return res
                    if not self.elevators[start]:
                        start = closest_elevator(start)
                        self.start_walk = True
                    if not self.elevators[end]:
                        end = closest_elevator(end)
                        self.end_walk = True
                    if not start or not end:
                        self.message = "Lo sentimos,\nno hay una ruta\naccesible para usted."
                        self.display_path([])
                        return

                change_penalty = 7 if (time in ["08h", "13h", "17h", "18h"] and day == "Lunes - Viernes") else 4
                path, self.est_time = astar(self.graph, start, end, change_penalty, self.positions)
                self.display_path(path)


if __name__ == "__main__":
    app = MetroApp()
    app.mainloop()
