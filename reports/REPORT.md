# Vidriera Insights — 09/10/2026

Análisis de **2,605 autos usados activos** (USD) de **35 automotoras** uruguayas,
a partir de los datos públicos de [Vidriera](https://vidriera-uy.vercel.app).

## 1. Marcas con más stock
![](brands.png)

| brand      |   listings |   median_price |   median_year |   median_km |
|:-----------|-----------:|---------------:|--------------:|------------:|
| Chevrolet  |        633 |          13290 |          2020 |       85667 |
| Renault    |        250 |          10990 |          2020 |       94034 |
| Fiat       |        191 |          10500 |          2018 |      105322 |
| Nissan     |        186 |          14990 |          2019 |       88648 |
| Volkswagen |        186 |          14295 |          2018 |       93709 |
| Peugeot    |        165 |          11400 |          2017 |      105000 |
| Hyundai    |        157 |          14990 |          2021 |       88214 |
| Suzuki     |        118 |          10900 |          2019 |       89037 |
| Citroën    |         92 |          11850 |          2019 |      104711 |
| Ford       |         92 |          12490 |          2017 |      108000 |
| Toyota     |         48 |          20245 |          2019 |      157277 |
| Geely      |         41 |          11490 |          2018 |       92338 |

## 2. Depreciación

### Curva general
Mediana del precio publicado según la antigüedad, como % de la mediana de los autos de **0–1 año que hoy
están en el stock usado** (no del precio de lista 0 km). Mezcla modelos distintos: los autos nuevos del
stock son más SUVs y marcas chinas que los viejos, así que la curva **exagera** la caída. Para comparar
autos de verdad, ver las tablas por modelo.

![](depreciation.png)

|   age |   listings |   median_price |   value_kept_pct |
|------:|-----------:|---------------:|-----------------:|
|     0 |         40 |          21990 |            103.5 |
|     1 |        121 |          20500 |             96.5 |
|     2 |        184 |          17990 |             84.7 |
|     3 |        219 |          16990 |             80   |
|     4 |        231 |          15990 |             75.3 |
|     5 |        158 |          16300 |             76.7 |
|     6 |        178 |          13890 |             65.4 |
|     7 |        178 |          12640 |             59.5 |
|     8 |        250 |          11990 |             56.4 |
|     9 |        161 |          10990 |             51.7 |
|    10 |        120 |          10990 |             51.7 |
|    11 |        132 |           9990 |             47   |
|    12 |        136 |           9890 |             46.6 |
|    13 |         97 |           9590 |             45.1 |
|    14 |         86 |           9895 |             46.6 |
|    15 |         72 |           9240 |             43.5 |

### Por modelo, separando edad y kilometraje
Dos regresiones log-lineales por modelo (autos de hasta 12 años, modelos con ≥20 publicaciones):

- `total_yearly_loss_pct`: `log(precio) ~ antigüedad`. La pérdida anual que ve un comprador, que mezcla
  envejecer y sumar kilómetros.
- `yearly_loss_pct`: `log(precio) ~ antigüedad + km`. La pérdida **solo por edad**, a igual kilometraje.
- `loss_per_10k_km_pct`: en la misma regresión, la pérdida por cada **10.000 km** extra a igual edad.

Un valor bajo significa que el modelo **retiene mejor su valor**. Muestras chicas dan coeficientes ruidosos
(un valor negativo en km indica justamente eso).

![](models.png)

| brand      | model    |   listings |   median_price |   yearly_loss_pct |   loss_per_10k_km_pct |   total_yearly_loss_pct |
|:-----------|:---------|-----------:|---------------:|------------------:|----------------------:|------------------------:|
| Volkswagen | Saveiro  |         25 |          15490 |              -0.6 |                   2.8 |                     2.9 |
| Citroën    | C3       |         32 |          11900 |               1.6 |                   2   |                     2.9 |
| Renault    | Sandero  |         24 |           9700 |               1.7 |                   2.2 |                     3.1 |
| Renault    | Kwid     |         53 |           9900 |               2.1 |                   0.8 |                     2.6 |
| Hyundai    | Hb20     |         57 |          13990 |               2.2 |                   2.8 |                     4.8 |
| Volkswagen | Gol      |         31 |          11900 |               2.4 |                   1.2 |                     2.9 |
| Chevrolet  | Joy      |         63 |          12290 |               2.6 |                   2.2 |                     4.2 |
| Nissan     | Kicks    |         45 |          17990 |               3   |                   3.1 |                     5.7 |
| Renault    | Duster   |         30 |          13390 |               3.2 |                   1.2 |                     4   |
| Fiat       | Strada   |         45 |          15690 |               3.6 |                   1.4 |                     5.2 |
| Chevrolet  | Onix     |        224 |          13990 |               3.7 |                   1.6 |                     5.2 |
| Suzuki     | Celerio  |         35 |          10990 |               3.8 |                   1.7 |                     4.8 |
| Chevrolet  | Prisma   |         39 |          10990 |               4   |                   1.1 |                     3.7 |
| Renault    | Oroch    |         44 |          15345 |               4.2 |                   1.6 |                     5.6 |
| Chevrolet  | Tracker  |         64 |          18640 |               4.4 |                   2.7 |                     6.6 |
| Fiat       | Uno      |         36 |           8900 |               4.5 |                   0.4 |                     4.1 |
| Peugeot    | 2008     |         27 |          14990 |               4.5 |                   1.7 |                     6.2 |
| Peugeot    | 208      |         61 |          13390 |               4.8 |                   1   |                     5.4 |
| Fiat       | Mobi     |         23 |          10900 |               5.1 |                   0.7 |                     5.5 |
| Ford       | Ecosport |         39 |          12900 |               6.7 |                  -0.7 |                     4.6 |
| Nissan     | Versa    |         33 |          16590 |               6.9 |                   0.7 |                     7.1 |
| Renault    | Stepway  |         21 |          10890 |             nan   |                 nan   |                     4.6 |

### Desde 0 km
Valor que conserva un usado frente a **lo que costaba 0 km el mismo modelo en su año**. Un Onix 2021 se
compara con el precio del Onix 0 km en 2021, no con el de hoy: los precios nuevos cambian bastante con los años y
usar el de hoy distorsiona la depreciación.

Los precios 0 km de cada año salen de la
[lista de Autoblog Uruguay](https://www.autoblog.com.uy/p/precios-0km.html) tal como la guardó el
[Internet Archive](https://web.archive.org/) a comienzos de cada año (2019–2026, 5,926
precios). Por ejemplo, la mediana de las versiones comparables del Onix:

|   year |   new_price |   base_price |   versions |
|-------:|------------:|-------------:|-----------:|
|   2019 |       17290 |        14490 |          5 |
|   2020 |       18440 |        16290 |          4 |
|   2021 |       19990 |        16490 |          9 |
|   2022 |       20490 |        16990 |          9 |
|   2023 |       21690 |        17990 |          9 |
|   2024 |       22390 |        17190 |          9 |
|   2025 |       22690 |        17490 |          9 |
|   2026 |       23490 |        18990 |          7 |

Solo cuentan versiones **comparables** (misma motorización que los usados y sin sub-modelos que casi no aparecen
entre ellos, como el Swift Sport). Se ajusta `log(precio usado / precio 0 km de su año) ~ antigüedad` por modelo y
se lee a 1, 3 y 5 años, **solo dentro de las edades que cubren los datos** (un hueco aparece vacío). Como no se sabe
la versión de cada usado, `kept_3y_pct` compara contra la versión mediana y `kept_3y_vs_base_pct` contra la más
barata: el valor real está entre las dos.

Una curva **plana** (igual % a 1, 3 y 5 años) no es un error: significa que los usados de ese modelo acompañaron
la suba de su precio 0 km, así que uno de 2019 vale, respecto de lo que costó, lo mismo que uno de 2024.

Límites: son precios de lista (sin las bonificaciones de las concesionarias, lo que exagera un poco la pérdida) y
precios publicados de usados (no de venta).

![](from_new.png)

| brand      | model    |   used_listings | years_covered   |   median_used_age |   kept_1y_pct |   kept_3y_pct |   kept_5y_pct |   kept_3y_vs_base_pct |
|:-----------|:---------|----------------:|:----------------|------------------:|--------------:|--------------:|--------------:|----------------------:|
| Suzuki     | Alto     |              10 | 2019–2023       |               5   |         nan   |          88.9 |          86.2 |                 100   |
| Fiat       | Mobi     |              15 | 2019–2026       |               7   |          92.6 |          87.9 |          83.4 |                  91.6 |
| Fiat       | Strada   |              32 | 2019–2026       |               4   |          87.9 |          84.9 |          82   |                  98.1 |
| Chevrolet  | Joy      |              14 | 2020–2022       |               5   |         nan   |          82.9 |          80.5 |                  82.9 |
| Volkswagen | Saveiro  |              20 | 2019–2026       |               3   |          79   |          81.8 |          84.7 |                  96.3 |
| Chevrolet  | Montana  |              23 | 2023–2025       |               2   |          84.8 |          74.6 |         nan   |                  88.8 |
| Geely      | Gx3      |              10 | 2020–2026       |               4   |          80.6 |          74.3 |          68.5 |                  76.8 |
| Volkswagen | Nivus    |              14 | 2021–2024       |               4.5 |          79.1 |          73.2 |          67.9 |                  78.2 |
| Chevrolet  | Onix     |             172 | 2019–2025       |               4   |          71.2 |          72.3 |          73.4 |                  87.2 |
| Chevrolet  | Captiva  |              12 | 2020–2023       |               4   |         nan   |          72.1 |          59.3 |                  76.8 |
| Renault    | Oroch    |              35 | 2019–2025       |               4   |          76.1 |          71.8 |          67.7 |                  79.7 |
| Volkswagen | Gol      |              11 | 2019–2023       |               4   |         nan   |          70.2 |          68.8 |                  73.5 |
| Renault    | Kwid     |              46 | 2019–2026       |               5   |          69.1 |          70   |          71   |                  75.8 |
| Hyundai    | Hb20     |              51 | 2019–2026       |               3   |          70.3 |          69.2 |          68.1 |                  96.9 |
| Chevrolet  | Tracker  |              48 | 2019–2026       |               4.5 |          72.6 |          69   |          65.6 |                  75.7 |
| Chevrolet  | Cruze    |              12 | 2019–2023       |               3.5 |         nan   |          67.9 |          60.9 |                  67.9 |
| Nissan     | Kicks    |              37 | 2019–2026       |               3   |          76.4 |          67.7 |          60   |                  73   |
| Chevrolet  | S10      |              13 | 2021–2026       |               2   |          68.2 |          64.6 |          61.2 |                 100   |
| Nissan     | Sentra   |              15 | 2020–2025       |               4   |          76   |          64.5 |          54.8 |                  70.4 |
| Citroën    | C4       |              16 | 2019–2025       |               4   |          73.7 |          63.6 |          55   |                  68.9 |
| Peugeot    | 208      |              40 | 2019–2025       |               3   |          71.8 |          62.3 |          54.1 |                  74.8 |
| Citroën    | C3       |              21 | 2019–2025       |               2   |          76.6 |          61.3 |          49.1 |                  69.6 |
| Renault    | Duster   |              16 | 2019–2025       |               4   |          57.2 |          56   |          54.8 |                  64.7 |
| Peugeot    | 2008     |              15 | 2019–2025       |               4   |          59   |          54.7 |          50.7 |                  74.9 |
| Ford       | Ecosport |              16 | 2019–2021       |               6.5 |         nan   |         nan   |          55.6 |                 nan   |


## 3. Kilometraje
A igual marca, modelo y año, cada **10.000 km extra** cambian el precio en **USD -192**.

## 4. Combustible y caja
El combustible se completa desde el título cuando el aviso no lo indica (por ejemplo "EV", "Híbrido",
"Seagull"), porque cerca de un cuarto de los avisos no lo cargan.

| fuel      |   listings |   median_price |   median_age |
|:----------|-----------:|---------------:|-------------:|
| Híbrido   |         36 |          34445 |            2 |
| Diésel    |         85 |          29500 |            6 |
| Eléctrico |         21 |          22990 |            1 |
| Nafta     |       1698 |          12990 |            7 |

| transmission   |   listings |   median_price |   median_age |
|:---------------|-----------:|---------------:|-------------:|
| Automática     |        446 |          18900 |            6 |
| Manual         |        824 |          10990 |            8 |

### Eléctricos e híbridos
| fuel      |   listings |   share_pct |   median_price |   median_year | top_brands                                              |
|:----------|-----------:|------------:|---------------:|--------------:|:--------------------------------------------------------|
| Eléctrico |         21 |        0.81 |          22990 |          2025 | Byd (7), Chevrolet (3), Bmw (2), Dongfeng (2)           |
| Híbrido   |         36 |        1.38 |          34445 |          2024 | Hyundai (12), Toyota (8), Mercedes-Benz (3), Suzuki (3) |

Los eléctricos usados son casi todos de **2024–2026**: el mercado de eléctricos de segunda mano en Uruguay
recién empieza. Con tan pocos autos no tiene sentido estimar su depreciación todavía; la sección 8 sigue
cómo crece su participación semana a semana.

| brand     | model    |   year |   mileage_km |   price | source_name          |
|:----------|:---------|-------:|-------------:|--------:|:---------------------|
| Dongfeng  | Nano     |   2024 |        57273 |   10900 | Arbeleche            |
| Changan   | E-Star   |   2024 |            1 |   12490 | Car One              |
| Byd       | Seagull  |   2025 |         6300 |   16500 | Amaya Motors         |
| Geely     | Geometry |   2026 |        29000 |   17990 | Moreira Automóviles  |
| Byd       | Seagull  |   2024 |        95000 |   17990 | Amaya Motors         |
| Byd       | Seagull  |   2025 |        22000 |   18990 | Mariño Sport         |
| Byd       | E2       |   2021 |        62400 |   18990 | Vipercar             |
| Chevrolet | Spark    |   2026 |        23000 |   20990 | Oliva Automotores    |
| Peugeot   | 208      |   2025 |        19927 |   20990 | Car One              |
| Jmc       | Jmev     |   2025 |           21 |   21990 | Car One              |
| Byd       | Yuan     |   2025 |        65000 |   22990 | Vladimir Automóviles |
| Dongfeng  | Mage     |   2026 |          nan |   24890 | Usados Fidocar       |
| Byd       | Yuan     |   2026 |        23080 |   26490 | López Motors         |
| Byd       | Yuan     |   2026 |        16000 |   27490 | Shopping Car         |
| Omoda     | E5       |   2025 |         3000 |   31200 | Moreira Automóviles  |
| Tesla     | Model    |   2022 |        65000 |   34990 | Vladimir Automóviles |
| Volvo     | C40      |   2022 |        35500 |   52990 | Amaya Motors         |
| Chevrolet | Equinox  |   2025 |        10617 |   58590 | Silca                |
| Chevrolet | Blazer   |   2025 |         7301 |   65990 | Silca                |
| Bmw       | Ix2      |   2025 |        37000 |   78900 | Grupo Fiancar        |
| Bmw       | I4       |   2024 |         4941 |   89900 | Arbeleche            |

## 5. Modelo de precio (machine learning)
Gradient boosting (`HistGradientBoostingRegressor`) sobre marca, modelo, combustible, caja, carrocería,
antigüedad y kilometraje, con objetivo `log(precio)`. Validación cruzada de 5 particiones:

| Métrica | Valor |
|---|---|
| Error medio (todos los autos) | **16.1%** (USD 2,729) |
| Error en autos con comparables — modelo | **11.0%** |
| Error en autos con comparables — precio justo de Vidriera | 10.5% |
| Autos que el método de comparables puede tasar | 57% |
| Error del modelo en autos **sin** comparables | 19.3% |

El modelo **iguala** al método de comparables donde éste funciona y además **tasa el 100% del stock**,
incluidos los modelos raros que no tienen suficientes autos parecidos.

![](predictions.png)

**Qué pesa más en el precio** (caída del R² al desordenar cada variable):

|              |   importancia_pct |
|:-------------|------------------:|
| age          |              43.3 |
| brand        |              22.8 |
| model        |              16.7 |
| mileage_km   |               6.2 |
| fuel         |               5.8 |
| transmission |               3.2 |
| body_type    |               1.9 |

**Candidatos a revisar**: autos del set de test publicados más por debajo de lo que espera el modelo
(una señal para mirar de cerca, no una garantía: el aviso puede tener detalles que los datos no capturan).

| brand      | model    |   year |   mileage_km |   price |   predicted |   discount_pct |
|:-----------|:---------|-------:|-------------:|--------:|------------:|---------------:|
| Volkswagen | Amarok   |   2021 |       144236 |   30990 |       66006 |           53   |
| Nissan     | Versa    |   2023 |        73158 |   11900 |       18495 |           35.7 |
| Peugeot    | 2008     |   2019 |        49252 |   12900 |       19743 |           34.7 |
| Chery      | Tiggo 2  |   2023 |        10657 |   14900 |       22743 |           34.5 |
| Renault    | Kangoo   |   2022 |       180863 |   10000 |       14892 |           32.8 |
| Hyundai    | Hb20     |   2019 |       130781 |    8990 |       13175 |           31.8 |
| Kia        | Picanto  |   2015 |        87839 |    8890 |       12785 |           30.5 |
| Ford       | Ecosport |   2017 |       155007 |   10490 |       15078 |           30.4 |
| Toyota     | Corolla  |   2010 |       204368 |    9900 |       14228 |           30.4 |
| Hyundai    | Hb20S    |   2021 |       100000 |   12900 |       17916 |           28   |

## 6. Cómo pone precio cada automotora
Negativo = más barata que autos comparables.
![](dealers.png)

| source_name                |   listings |   median_vs_fair_pct |   share_above_fair |
|:---------------------------|-----------:|---------------------:|-------------------:|
| Kaitazoff                  |         12 |               -10.65 |               25   |
| Automotora Barriola        |         26 |                -8.7  |                7.7 |
| Motorlider                 |         39 |                -8.3  |                2.6 |
| Autoventas                 |         12 |                -8.05 |               25   |
| Facilcar                   |         13 |                -7.7  |               23.1 |
| Shopping Car               |         17 |                -7.6  |               11.8 |
| Gonzalo Ruiz Automóviles   |         20 |                -7.45 |               20   |
| Silca                      |        112 |                -6.5  |               15.2 |
| Shopping de Autos          |         95 |                -6.4  |                9.5 |
| Kleist Automóviles         |         11 |                -5.1  |               36.4 |
| Grupo Fiancar              |         64 |                -4.4  |               18.8 |
| Mariño Sport               |         24 |                -4.35 |               16.7 |
| AG Automóviles             |         13 |                -2.4  |               30.8 |
| Vipercar                   |        114 |                -1.8  |               24.6 |
| Arbeleche                  |         12 |                -1    |               41.7 |
| Iriondo Automotors         |         22 |                -0.5  |               31.8 |
| LR Automóviles             |         12 |                -0.5  |               33.3 |
| Vladimir Automóviles       |         22 |                -0.45 |               31.8 |
| Usados Fidocar             |         68 |                -0.4  |               32.4 |
| Moreira Automóviles        |         14 |                -0.25 |               14.3 |
| Carper Usados              |        300 |                 0    |               31   |
| Car One                    |        147 |                 1.3  |               38.8 |
| Amaya Motors               |         28 |                 1.8  |               46.4 |
| Julio Automóviles          |         70 |                 7.1  |               57.1 |
| Drivers                    |         13 |                 8.2  |               61.5 |
| Nicolás Tejera Automóviles |        124 |                10.1  |               63.7 |
| Renato Conti               |         10 |                13.95 |               80   |
| Chevrolet Florida          |         31 |                16.4  |               80.6 |

## 7. ¿Los autos caros tardan más en venderse?
| bucket    |   listings |   median_days |   share_with_price_cut |
|:----------|-----------:|--------------:|-----------------------:|
| <-10%     |        291 |             2 |                    0.7 |
| -10 a -2% |        381 |             2 |                    2.4 |
| ±2%       |        215 |             2 |                    0.9 |
| +2 a +10% |        292 |             2 |                    2.4 |
| >+10%     |        314 |             2 |                    0.3 |

> Vidriera registra datos desde el 07/10/2026: esta tabla gana sentido
> a medida que se acumulan semanas de historia (días publicados y rebajas de precio).

## 8. Evolución del mercado
Stock, precio mediano y % de eléctricos e híbridos en cada foto semanal.

_Se necesita más de una corrida con `--refresh` para ver la evolución._
