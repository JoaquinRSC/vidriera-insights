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

### Por modelo
Pendiente de `log(precio) ~ antigüedad` por modelo (autos de hasta 12 años, modelos con ≥20 publicaciones).
Un valor bajo significa que el modelo **retiene mejor su valor**.

![](models.png)

| brand      | model    |   listings |   median_price |   yearly_loss_pct |
|:-----------|:---------|-----------:|---------------:|------------------:|
| Volkswagen | Gol      |         27 |          11900 |               2.4 |
| Citroën    | C3       |         28 |          11900 |               2.6 |
| Renault    | Kwid     |         42 |           9895 |               2.7 |
| Renault    | Sandero  |         24 |           9700 |               3.1 |
| Hyundai    | Hb20     |         46 |          14990 |               3.5 |
| Chevrolet  | Prisma   |         38 |          10990 |               3.7 |
| Renault    | Duster   |         26 |          12890 |               4.1 |
| Chevrolet  | Joy      |         63 |          12290 |               4.2 |
| Fiat       | Uno      |         35 |           8900 |               4.3 |
| Ford       | Ecosport |         34 |          13245 |               4.5 |
| Suzuki     | Celerio  |         27 |          11490 |               4.8 |
| Peugeot    | 208      |         53 |          13500 |               5.2 |
| Fiat       | Strada   |         45 |          15690 |               5.2 |
| Chevrolet  | Onix     |        209 |          13990 |               5.3 |
| Fiat       | Mobi     |         20 |          10150 |               5.4 |
| Nissan     | Kicks    |         35 |          18990 |               6   |
| Renault    | Oroch    |         39 |          15490 |               6.1 |
| Peugeot    | 2008     |         23 |          14990 |               6.4 |
| Chevrolet  | Tracker  |         62 |          18390 |               6.5 |
| Nissan     | Versa    |         30 |          16245 |               7.2 |

## 3. Kilometraje
A igual marca, modelo y año, cada **10.000 km extra** cambian el precio en **USD -193**.

## 4. Combustible y caja
| fuel      |   listings |   median_price |   median_age |
|:----------|-----------:|---------------:|-------------:|
| Híbrido   |         21 |          31500 |            3 |
| Diésel    |         78 |          28745 |            7 |
| Eléctrico |         17 |          21990 |            1 |
| Nafta     |       1569 |          12990 |            7 |

| transmission   |   listings |   median_price |   median_age |
|:---------------|-----------:|---------------:|-------------:|
| Automática     |        383 |          18490 |            5 |
| Manual         |        740 |          10990 |            8 |

## 5. Modelo de precio (machine learning)
Gradient boosting (`HistGradientBoostingRegressor`) sobre marca, modelo, combustible, caja, carrocería,
antigüedad y kilometraje, con objetivo `log(precio)`. Validación cruzada de 5 particiones:

| Métrica | Valor |
|---|---|
| Error medio (todos los autos) | **15.8%** (USD 2,643) |
| Error en autos con comparables — modelo | **10.6%** |
| Error en autos con comparables — precio justo de Vidriera | 10.6% |
| Autos que el método de comparables puede tasar | 56% |
| Error del modelo en autos **sin** comparables | 23.5% |

El modelo **iguala** al método de comparables donde éste funciona y además **tasa el 100% del stock**,
incluidos los modelos raros que no tienen suficientes autos parecidos.

![](predictions.png)

**Qué pesa más en el precio** (caída del R² al desordenar cada variable):

|              |   importancia_pct |
|:-------------|------------------:|
| age          |              43.4 |
| brand        |              22.8 |
| model        |              15.8 |
| fuel         |               8.8 |
| mileage_km   |               5.4 |
| transmission |               2.9 |
| body_type    |               0.9 |

**Candidatos a revisar**: autos del set de test publicados más por debajo de lo que espera el modelo
(una señal para mirar de cerca, no una garantía: el aviso puede tener detalles que los datos no capturan).

| brand      | model    |   year |   mileage_km |   price |   predicted |   discount_pct |
|:-----------|:---------|-------:|-------------:|--------:|------------:|---------------:|
| Volkswagen | Polo     |   2025 |        20407 |   16490 |       31137 |           47   |
| Renault    | Oroch    |   2020 |       167742 |    9990 |       17640 |           43.4 |
| Volkswagen | Polo     |   2022 |       127380 |   15500 |       26218 |           40.9 |
| Peugeot    | 208      |   2020 |       184467 |   10200 |       15730 |           35.2 |
| Toyota     | Hilux    |   2014 |       255593 |   16900 |       25460 |           33.6 |
| Nissan     | Frontier |   2024 |        79479 |   27990 |       41450 |           32.5 |
| Hyundai    | H1       |   2010 |       350000 |    7990 |       11707 |           31.7 |
| Peugeot    | 2008     |   2019 |        49252 |   12900 |       18898 |           31.7 |
| Gwm        | Wingle 5 |   2015 |       262407 |    7800 |       11389 |           31.5 |
| Chery      | Tiggo 2  |   2023 |        10657 |   14900 |       21504 |           30.7 |

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
_Se necesita más de una corrida con `--refresh` para ver la evolución._
