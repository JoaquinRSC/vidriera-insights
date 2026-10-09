# Vidriera Insights — 09/10/2026

Análisis de **2,303 autos usados activos** (USD) de **27 automotoras** uruguayas,
a partir de los datos públicos de [Vidriera](https://vidriera-uy.vercel.app).

## 1. Marcas con más stock
![](brands.png)

| brand      |   listings |   median_price |   median_year |   median_km |
|:-----------|-----------:|---------------:|--------------:|------------:|
| Chevrolet  |        597 |          13490 |          2020 |       84424 |
| Renault    |        226 |          10990 |          2019 |       96049 |
| Fiat       |        184 |          10650 |          2018 |      106000 |
| Nissan     |        162 |          14700 |          2019 |       87340 |
| Volkswagen |        141 |          13900 |          2018 |       89617 |
| Hyundai    |        137 |          14990 |          2021 |       83705 |
| Peugeot    |        133 |          11890 |          2018 |      100792 |
| Suzuki     |         95 |          10990 |          2019 |       89000 |
| Citroën    |         84 |          11850 |          2019 |      106262 |
| Ford       |         78 |          12895 |          2017 |      112030 |
| Toyota     |         44 |          20245 |          2019 |      160000 |
| Geely      |         37 |          11890 |          2020 |       91048 |

## 2. Depreciación

### Curva general
Mediana del precio publicado según la antigüedad, como % de la mediana de los autos de **0–1 año que hoy
están en el stock usado** (no del precio de lista 0 km). Mezcla modelos distintos: los autos nuevos del
stock son más SUVs y marcas chinas que los viejos, así que la curva **exagera** la caída. Para comparar
autos de verdad, ver las tablas por modelo.

![](depreciation.png)

|   age |   listings |   median_price |   value_kept_pct |
|------:|-----------:|---------------:|-----------------:|
|     0 |         34 |          20740 |             99.4 |
|     1 |         99 |          20990 |            100.6 |
|     2 |        159 |          17590 |             84.3 |
|     3 |        203 |          16990 |             81.4 |
|     4 |        210 |          15990 |             76.6 |
|     5 |        140 |          16440 |             78.8 |
|     6 |        158 |          13640 |             65.4 |
|     7 |        159 |          12890 |             61.8 |
|     8 |        222 |          11990 |             57.5 |
|     9 |        145 |          10900 |             52.2 |
|    10 |        105 |          10900 |             52.2 |
|    11 |        121 |           9990 |             47.9 |
|    12 |        119 |           9890 |             47.4 |
|    13 |         85 |           9990 |             47.9 |
|    14 |         75 |           9900 |             47.4 |
|    15 |         63 |           8990 |             43.1 |

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
| Citroën    | C3       |         28 |          11900 |               1.6 |                   1.7 |                     2.6 |
| Renault    | Sandero  |         24 |           9700 |               1.7 |                   2.2 |                     3.1 |
| Hyundai    | Hb20     |         46 |          14990 |               1.7 |                   2.1 |                     3.5 |
| Volkswagen | Gol      |         27 |          11900 |               2.1 |                   0.9 |                     2.4 |
| Renault    | Kwid     |         42 |           9895 |               2.3 |                   1   |                     2.7 |
| Chevrolet  | Joy      |         63 |          12290 |               2.6 |                   2.2 |                     4.2 |
| Renault    | Duster   |         26 |          12890 |               3.5 |                   1.3 |                     4.1 |
| Fiat       | Strada   |         45 |          15690 |               3.6 |                   1.4 |                     5.2 |
| Suzuki     | Celerio  |         27 |          11490 |               3.8 |                   1.7 |                     4.8 |
| Chevrolet  | Onix     |        209 |          13990 |               3.8 |                   1.7 |                     5.3 |
| Chevrolet  | Prisma   |         38 |          10990 |               4   |                   1.1 |                     3.7 |
| Nissan     | Kicks    |         35 |          18990 |               4.3 |                   1.9 |                     6   |
| Chevrolet  | Tracker  |         62 |          18390 |               4.3 |                   2.6 |                     6.5 |
| Peugeot    | 2008     |         23 |          14990 |               4.4 |                   1.8 |                     6.4 |
| Peugeot    | 208      |         53 |          13500 |               4.6 |                   1.1 |                     5.2 |
| Renault    | Oroch    |         39 |          15490 |               4.6 |                   1.6 |                     6.1 |
| Fiat       | Uno      |         35 |           8900 |               5.5 |                   0.5 |                     4.3 |
| Ford       | Ecosport |         34 |          13245 |               6.8 |                  -0.7 |                     4.5 |
| Nissan     | Versa    |         30 |          16245 |               7.3 |                   0.5 |                     7.2 |
| Fiat       | Mobi     |         20 |          10150 |             nan   |                 nan   |                     5.4 |

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
| Fiat       | Mobi     |              14 | 2019–2026       |               7   |          90.8 |          86.4 |          82.1 |                  90   |
| Fiat       | Strada   |              32 | 2019–2026       |               4   |          87.9 |          84.9 |          82   |                  98.1 |
| Chevrolet  | Joy      |              14 | 2020–2022       |               5   |         nan   |          82.9 |          80.5 |                  82.9 |
| Volkswagen | Saveiro  |              15 | 2019–2026       |               3   |          76.9 |          80   |          83.2 |                  94.2 |
| Chevrolet  | Montana  |              22 | 2023–2025       |               2   |          85   |          75.5 |         nan   |                  89.9 |
| Geely      | Gx3      |              10 | 2020–2026       |               4   |          80.6 |          74.3 |          68.5 |                  76.8 |
| Renault    | Oroch    |              32 | 2019–2025       |               4   |          79.8 |          73.5 |          67.8 |                  81.6 |
| Chevrolet  | Onix     |             162 | 2019–2025       |               4   |          71.8 |          72.8 |          73.9 |                  87.8 |
| Chevrolet  | Captiva  |              12 | 2020–2023       |               4   |         nan   |          72.1 |          59.3 |                  76.8 |
| Volkswagen | Nivus    |              12 | 2021–2024       |               5   |          75.4 |          71.6 |          68   |                  75.6 |
| Volkswagen | Gol      |              10 | 2020–2023       |               4   |         nan   |          70.6 |          68.4 |                  73.9 |
| Renault    | Kwid     |              36 | 2019–2026       |               5   |          69.5 |          70.5 |          71.5 |                  76.4 |
| Hyundai    | Hb20     |              44 | 2019–2026       |               3   |          69.5 |          70.2 |          70.8 |                  98.3 |
| Nissan     | Kicks    |              29 | 2019–2026       |               3   |          78.8 |          69.8 |          61.8 |                  75.2 |
| Nissan     | Versa    |              21 | 2020–2025       |               3   |          67.5 |          69.6 |          71.8 |                  80.6 |
| Chevrolet  | Tracker  |              46 | 2019–2026       |               5   |          71.1 |          68.3 |          65.6 |                  74.7 |
| Chevrolet  | Cruze    |              12 | 2019–2023       |               3.5 |         nan   |          67.9 |          60.9 |                  67.9 |
| Chevrolet  | S10      |              11 | 2021–2026       |               2   |          70.5 |          65   |          60   |                 100   |
| Nissan     | Sentra   |              14 | 2020–2025       |               4   |          72.2 |          63.4 |          55.6 |                  69.2 |
| Citroën    | C4       |              15 | 2019–2025       |               4   |          73.3 |          63.4 |          54.9 |                  68.7 |
| Peugeot    | 208      |              36 | 2019–2025       |               3   |          72.3 |          62.6 |          54.3 |                  75.2 |
| Citroën    | C3       |              17 | 2019–2025       |               2   |          76.8 |          61.3 |          48.9 |                  69.6 |
| Renault    | Duster   |              12 | 2019–2025       |               4   |          60.2 |          57.4 |          54.7 |                  66.3 |
| Peugeot    | 2008     |              12 | 2019–2024       |               4   |          59   |          55.2 |          51.6 |                  75.6 |
| Ford       | Ecosport |              14 | 2019–2021       |               6.5 |         nan   |         nan   |          55.6 |                 nan   |


## 3. Kilometraje
A igual marca, modelo y año, cada **10.000 km extra** cambian el precio en **USD -193**.

## 4. Combustible y caja
El combustible se completa desde el título cuando el aviso no lo indica (por ejemplo "EV", "Híbrido",
"Seagull"), porque cerca de un cuarto de los avisos no lo cargan.

| fuel      |   listings |   median_price |   median_age |
|:----------|-----------:|---------------:|-------------:|
| Híbrido   |         33 |          34900 |            2 |
| Diésel    |         78 |          28745 |            7 |
| Eléctrico |         19 |          21990 |            1 |
| Nafta     |       1569 |          12990 |            7 |

| transmission   |   listings |   median_price |   median_age |
|:---------------|-----------:|---------------:|-------------:|
| Automática     |        383 |          18490 |            5 |
| Manual         |        740 |          10990 |            8 |

### Eléctricos e híbridos
| fuel      |   listings |   share_pct |   median_price |   median_year | top_brands                                              |
|:----------|-----------:|------------:|---------------:|--------------:|:--------------------------------------------------------|
| Eléctrico |         19 |        0.83 |          21990 |          2025 | Byd (6), Chevrolet (3), Bmw (2), Dongfeng (2)           |
| Híbrido   |         33 |        1.43 |          34900 |          2024 | Hyundai (11), Toyota (7), Mercedes-Benz (3), Suzuki (3) |

Los eléctricos usados son casi todos de **2024–2026**: el mercado de eléctricos de segunda mano en Uruguay
recién empieza. Con tan pocos autos no tiene sentido estimar su depreciación todavía; la sección 8 sigue
cómo crece su participación semana a semana.

| brand     | model    |   year |   mileage_km |   price | source_name         |
|:----------|:---------|-------:|-------------:|--------:|:--------------------|
| Dongfeng  | Nano     |   2024 |        57273 |   10900 | Arbeleche           |
| Changan   | E-Star   |   2024 |            1 |   12490 | Car One             |
| Byd       | Seagull  |   2025 |         6300 |   16500 | Amaya Motors        |
| Geely     | Geometry |   2026 |        29000 |   17990 | Moreira Automóviles |
| Byd       | Seagull  |   2024 |        95000 |   17990 | Amaya Motors        |
| Byd       | Seagull  |   2025 |        22000 |   18990 | Mariño Sport        |
| Byd       | E2       |   2021 |        62400 |   18990 | Vipercar            |
| Chevrolet | Spark    |   2026 |        23000 |   20990 | Oliva Automotores   |
| Peugeot   | 208      |   2025 |        19927 |   20990 | Car One             |
| Jmc       | Jmev     |   2025 |           21 |   21990 | Car One             |
| Dongfeng  | Mage     |   2026 |          nan |   24890 | Usados Fidocar      |
| Byd       | Yuan     |   2026 |        23080 |   26490 | López Motors        |
| Byd       | Yuan     |   2026 |        16000 |   27490 | Shopping Car        |
| Omoda     | E5       |   2025 |         3000 |   31200 | Moreira Automóviles |
| Volvo     | C40      |   2022 |        35500 |   52990 | Amaya Motors        |
| Chevrolet | Equinox  |   2025 |        10617 |   58590 | Silca               |
| Chevrolet | Blazer   |   2025 |         7301 |   65990 | Silca               |
| Bmw       | Ix2      |   2025 |        37000 |   78900 | Grupo Fiancar       |
| Bmw       | I4       |   2024 |         4941 |   89900 | Arbeleche           |

## 5. Modelo de precio (machine learning)
Gradient boosting (`HistGradientBoostingRegressor`) sobre marca, modelo, combustible, caja, carrocería,
antigüedad y kilometraje, con objetivo `log(precio)`. Validación cruzada de 5 particiones:

| Métrica | Valor |
|---|---|
| Error medio (todos los autos) | **15.9%** (USD 2,648) |
| Error en autos con comparables — modelo | **10.6%** |
| Error en autos con comparables — precio justo de Vidriera | 10.6% |
| Autos que el método de comparables puede tasar | 56% |
| Error del modelo en autos **sin** comparables | 23.9% |

El modelo **iguala** al método de comparables donde éste funciona y además **tasa el 100% del stock**,
incluidos los modelos raros que no tienen suficientes autos parecidos.

![](predictions.png)

**Qué pesa más en el precio** (caída del R² al desordenar cada variable):

|              |   importancia_pct |
|:-------------|------------------:|
| age          |              42.1 |
| brand        |              21.9 |
| model        |              16.2 |
| fuel         |               9.1 |
| mileage_km   |               6   |
| transmission |               3.5 |
| body_type    |               1.2 |

**Candidatos a revisar**: autos del set de test publicados más por debajo de lo que espera el modelo
(una señal para mirar de cerca, no una garantía: el aviso puede tener detalles que los datos no capturan).

| brand      | model    |   year |   mileage_km |   price |   predicted |   discount_pct |
|:-----------|:---------|-------:|-------------:|--------:|------------:|---------------:|
| Volkswagen | Polo     |   2025 |        20407 |   16490 |       31015 |           46.8 |
| Volkswagen | Polo     |   2022 |       127380 |   15500 |       26517 |           41.5 |
| Renault    | Oroch    |   2020 |       167742 |    9990 |       16176 |           38.2 |
| Chery      | Tiggo 2  |   2023 |        10657 |   14900 |       23046 |           35.3 |
| Toyota     | Hilux    |   2014 |       255593 |   16900 |       25650 |           34.1 |
| Nissan     | Frontier |   2024 |        79479 |   27990 |       42116 |           33.5 |
| Peugeot    | 208      |   2020 |       184467 |   10200 |       14778 |           31   |
| Jeep       | Renegade |   2021 |       123000 |   14990 |       21646 |           30.7 |
| Hyundai    | H1       |   2010 |       350000 |    7990 |       11499 |           30.5 |
| Peugeot    | 2008     |   2019 |        49252 |   12900 |       18338 |           29.7 |

## 6. Cómo pone precio cada automotora
Negativo = más barata que autos comparables.
![](dealers.png)

| source_name                |   listings |   median_vs_fair_pct |   share_above_fair |
|:---------------------------|-----------:|---------------------:|-------------------:|
| Kaitazoff                  |         12 |               -10.95 |               25   |
| Autoventas                 |         10 |                -8.9  |               20   |
| Shopping de Autos          |         93 |                -7.4  |                9.7 |
| Silca                      |        109 |                -6.8  |               14.7 |
| Gonzalo Ruiz Automóviles   |         16 |                -6.45 |               12.5 |
| Facilcar                   |         12 |                -5.55 |               25   |
| Grupo Fiancar              |         61 |                -5.4  |               18   |
| Mariño Sport               |         23 |                -4.7  |               17.4 |
| Shopping Car               |         15 |                -3.2  |               13.3 |
| Vipercar                   |        108 |                -2.1  |               22.2 |
| Arbeleche                  |         12 |                -1.7  |               41.7 |
| Moreira Automóviles        |         14 |                -1.1  |               21.4 |
| Usados Fidocar             |         64 |                -0.95 |               28.1 |
| Car One                    |        138 |                 0    |               34.8 |
| Carper Usados              |        292 |                 0    |               30.1 |
| Kleist Automóviles         |         11 |                 0    |               36.4 |
| Amaya Motors               |         26 |                 4.3  |               50   |
| Drivers                    |         13 |                 5.9  |               53.8 |
| Julio Automóviles          |         67 |                 6.9  |               55.2 |
| Nicolás Tejera Automóviles |        117 |                10.5  |               66.7 |
| Chevrolet Florida          |         31 |                15.9  |               77.4 |

## 7. ¿Los autos caros tardan más en venderse?
| bucket    |   listings |   median_days |   share_with_price_cut |
|:----------|-----------:|--------------:|-----------------------:|
| <-10%     |        262 |             2 |                    1.1 |
| -10 a -2% |        319 |             2 |                    2.8 |
| ±2%       |        183 |             2 |                    0.5 |
| +2 a +10% |        245 |             2 |                    2.9 |
| >+10%     |        271 |             2 |                    0.4 |

> Vidriera registra datos desde el 07/10/2026: esta tabla gana sentido
> a medida que se acumulan semanas de historia (días publicados y rebajas de precio).

## 8. Evolución del mercado
Stock, precio mediano y % de eléctricos e híbridos en cada foto semanal.

_Se necesita más de una corrida con `--refresh` para ver la evolución._
