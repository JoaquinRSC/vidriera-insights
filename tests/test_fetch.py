from vidriera_insights.fetch import parse_new_car_prices

PAGE = """
<p>Última actualización: <b>12</b><strong>/10/2026</strong></p>
<section class="ab-price-brand" data-brand="CHEVROLET" data-search="chevrolet" id="marca-chevrolet">
  <ul class="ab-price-models">
    <li><span class="ab-price-model"><a href="#">Onix 1.0 Turbo LT</a></span>
        <strong class="ab-price-value">U$S 21.490</strong></li>
    <li><span class="ab-price-model">Tracker  1.2 Turbo   Premier</span>
        <strong class="ab-price-value">U$S 32.890</strong></li>
  </ul>
</section>
<section class="ab-price-brand" data-brand="CITRO&Euml;N" id="marca-citroen">
  <ul class="ab-price-models">
    <li><span class="ab-price-model">C3 1.6 Feel</span><strong class="ab-price-value">U$S 17.990</strong></li>
  </ul>
</section>
"""


def test_parse_new_car_prices_reads_brands_names_prices_and_date():
    df = parse_new_car_prices(PAGE)
    assert df["brand"].tolist() == ["Chevrolet", "Chevrolet", "Citroën"]
    assert df["name"].tolist() == ["Onix 1.0 Turbo LT", "Tracker 1.2 Turbo Premier", "C3 1.6 Feel"]
    assert df["price"].tolist() == [21490.0, 32890.0, 17990.0]
    assert set(df["list_updated"]) == {"2026-10-12"}
