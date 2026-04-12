import pydot

# Загружаем .dot файл
graphs = pydot.graph_from_dot_file('my_project.dot')
graph = graphs[0]

# Сохраняем в PNG
graph.write_png('models.png')
graph.write_svg('models.svg')

print("Готово! models.png и models.svg созданы")