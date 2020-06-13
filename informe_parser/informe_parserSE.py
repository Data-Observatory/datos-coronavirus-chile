import camelot
import json
import csv
from collections import OrderedDict

INPUT_DATE = "2020-05-29"
INPUT_HEADER = "SE16"


def load_json(file_name):
    with open(file_name) as json_file:
        return json.load(json_file)


class InformeParser:
    def load_input(self):
        # Load comunas names (es, en, extra)
        self.comunas_en = load_json("../names/comunas_en.json")
        self.comunas_es = load_json("../names/comunas_es.json")
        self.comunas_extra = load_json("../names/comunas_extra.json")
        self.all_comunas = {*self.comunas_es, *self.comunas_en, *self.comunas_extra}
        # Load fixed comunas names
        self.fixed_comunas = {
            **load_json("../names/fixed_comunas.json"),
            **load_json("../names/fixed_comunas_extra.json")
        }

    def parse_tables(self):
        self.tables = camelot.read_pdf(
            "./input/tablas_informe_{}.pdf".format(INPUT_DATE),
            pages="all",
            flavor="stream",
            strip_text="&",
        )

    def fix_comuna(self, comuna):
        if comuna in self.fixed_comunas:
            return self.fixed_comunas[comuna]
        return comuna

    def scrap_casos_por_comuna(self,i):
        self.casos_por_comuna = OrderedDict({comuna: None for comuna in self.comunas_es})
        for table in self.tables:
            for row in table.df.itertuples(index=True, name="Pandas"):
                if row[1] in self.all_comunas:
                    nombre_comuna = self.fix_comuna(row[1])
                    casos_comuna = row[i]
                    jump = row[i].find('\n')
                    if jump != -1: print(nombre_comuna,' tiene el salto',row[i][:jump]) 
                    if jump != -1: casos_comuna = row[i][:jump]
                    self.casos_por_comuna[nombre_comuna] = casos_comuna
                    print(row[0],nombre_comuna,casos_comuna)

    def save_casos_por_comuna(self):
        casos_por_comuna_data = [
            {"comuna": comuna, "confirmados": casos}
            for comuna, casos in self.casos_por_comuna.items()
        ]
        with open("./output/FechaInicioSintomas_por_comuna_{}.csv".format(INPUT_DATE), "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["comuna", "confirmados"])
            writer.writeheader()
            for data in casos_por_comuna_data:
                writer.writerow(data)

    def merge(self):
        #last_data_path = "../minciencia_data/TasaDeIncidenciaPorComuna.csv"
        last_data_path = "../minciencia_data/FechaInicioSintomas8.csv"
        with open(last_data_path, 'r') as csv_file:
            reader = iter(list(csv.reader(csv_file)))
        with open(last_data_path, 'w') as csv_file:
            writer = csv.writer(csv_file, lineterminator='\n')
            # Add new informe's date header
            new_rows = []
            header = next(reader)
            header.append(INPUT_HEADER)
            new_rows.append(header)
            # Add comunas' new casos
            region_casos = 0
            for row in reader:
                if row[2] != "Total":
                    comuna = self.fix_comuna(row[2])
                    self.casos_por_comuna[comuna]=self.casos_por_comuna[comuna].replace(".", "")
                    self.casos_por_comuna[comuna]=self.casos_por_comuna[comuna].replace(",", ".")
                    #print(comuna,self.casos_por_comuna[comuna])
                    comuna_casos = float(self.casos_por_comuna[comuna]) if self.casos_por_comuna[comuna] else 0
                    row.append(comuna_casos)
                    region_casos += comuna_casos
                else:
                    row.append(region_casos)
                    region_casos = 0
                new_rows.append(row)
            # Write new rows
            writer.writerows(new_rows)


parser = InformeParser()
parser.load_input()
parser.parse_tables()
parser.scrap_casos_por_comuna(16)
parser.save_casos_por_comuna()
parser.merge()
