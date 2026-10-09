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


OLD_PAGE = """
<div class="separator"><a href="https://1.bp.blogspot.com/x/Chevrolet-logo-2013.jpg"><img src="x"/></a></div>
<div><b>Importador: General Motors Uruguay.</b></div><div><b>Web:</b> www.chevrolet.com.uy</div>
<ul><li><a href="#"><b>Onix</b> LS 1.2</a> - 16.990</li>
<li><a href="#"><b>Joy Plus</b>&nbsp;1.0</a><span style="text-align: start;">&nbsp;- 15.290</span></li></ul>
<div class="separator"><a href="https://1.bp.blogspot.com/x/Citroen-logo.png"><img src="x"/></a></div>
<div><b>Importador: Sevel Uruguay.</b></div>
<ul><li><a href="#"><b>C3</b> 1.6 Feel</a> - 15.990</li></ul>
"""


def test_parse_archived_prices_reads_the_old_blog_layout():
    from vidriera_insights.fetch import parse_archived_prices

    df = parse_archived_prices(OLD_PAGE, ["Chevrolet", "Citroën", "Fiat"])
    assert df.to_dict("records") == [
        {"brand": "Chevrolet", "name": "Onix LS 1.2", "price": 16990.0},
        {"brand": "Chevrolet", "name": "Joy Plus 1.0", "price": 15290.0},
        {"brand": "Citroën", "name": "C3 1.6 Feel", "price": 15990.0},
    ]


def test_parse_archived_prices_falls_back_to_the_current_layout():
    from vidriera_insights.fetch import parse_archived_prices

    assert parse_archived_prices(PAGE, ["Chevrolet"])["name"].tolist()[0] == "Onix 1.0 Turbo LT"
