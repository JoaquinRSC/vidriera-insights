// Price estimator: reads the grid exported by `python -m vidriera_insights.export`
// and interpolates between mileage grid points for the selected year.

const usd = new Intl.NumberFormat('es-UY', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const num = new Intl.NumberFormat('es-UY')
const pct = (v) => new Intl.NumberFormat('es-UY', { maximumFractionDigits: 1 }).format(v)
const $ = (id) => document.getElementById(id)

let data
let chart

// Dealer names, models and URLs come from scraped listings: escape before building HTML.
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
const safeUrl = (url) => (typeof url === 'string' && /^https?:\/\//i.test(url) ? escapeHtml(url) : null)

function modelsOf(brand) {
  return data.models.filter((m) => m.brand === brand)
}

function current() {
  return data.models.find((m) => m.brand === $('brand').value && m.model === $('model').value)
}

function fillSelect(select, values, selected) {
  select.replaceChildren(...values.map((v) => new Option(v, v)))
  if (selected !== undefined && values.includes(selected)) select.value = selected
}

// Linear interpolation over the km grid for one year row of a price matrix.
function priceAt(matrix, entry, yearIndex, km) {
  const kms = entry.km
  const clamped = Math.min(Math.max(km, kms[0]), kms[kms.length - 1])
  let i = kms.findIndex((k) => k >= clamped)
  if (i <= 0) return matrix[yearIndex][0]
  const t = (clamped - kms[i - 1]) / (kms[i] - kms[i - 1])
  return matrix[yearIndex][i - 1] * (1 - t) + matrix[yearIndex][i] * t
}

function estimate(entry, year, km) {
  const y = entry.years.indexOf(year)
  return {
    low: priceAt(entry.low, entry, y, km),
    mid: priceAt(entry.mid, entry, y, km),
    high: priceAt(entry.high, entry, y, km),
  }
}

function onBrand() {
  const models = modelsOf($('brand').value).map((m) => m.model)
  fillSelect($('model'), models, $('model').value)
  onModel()
}

function onModel() {
  const entry = current()
  const years = [...entry.years].reverse().map(String)
  const typicalYear = String(entry.years[Math.floor(entry.years.length * 0.6)] ?? entry.years.at(-1))
  fillSelect($('year'), years, years.includes($('year').value) ? $('year').value : typicalYear)
  const maxKm = entry.km.at(-1)
  $('km').max = maxKm
  $('km-number').max = maxKm
  if (Number($('km').value) > maxKm) setKm(Math.round(maxKm / 2))
  render()
}

function setKm(value) {
  $('km').value = value
  $('km-number').value = value
}

function chip(html) {
  const span = document.createElement('span')
  span.className = 'chip'
  span.innerHTML = html
  return span
}

function render() {
  const entry = current()
  const year = Number($('year').value)
  const km = Number($('km').value)
  const { low, mid, high } = estimate(entry, year, km)

  $('result-title').textContent = `${entry.brand} ${entry.model} ${year} · ${num.format(km)} km`
  $('price').textContent = usd.format(Math.round(mid / 10) * 10)
  $('low').textContent = usd.format(Math.round(low / 10) * 10)
  $('high').textContent = usd.format(Math.round(high / 10) * 10)
  $('range-dot').style.left = `${((mid - low) / (high - low)) * 100}%`

  const chips = []
  const d = entry.depreciation
  if (d?.yearly_loss_pct != null) {
    chips.push(chip(`Pierde <strong>${pct(d.yearly_loss_pct)}%</strong> por año de antigüedad`))
    if (d.loss_per_10k_km_pct > 0) chips.push(chip(`y <strong>${pct(d.loss_per_10k_km_pct)}%</strong> cada 10.000 km`))
  }
  const newThen = entry.new_by_year?.[String(year)]
  if (newThen) {
    chips.push(chip(`0 km en ${year}: <strong>${usd.format(newThen)}</strong> · hoy vale <strong>${Math.round((mid / newThen) * 100)}%</strong>`))
  }
  const kept = entry.from_new?.kept_3y_pct
  if (kept != null) {
    const high = entry.from_new.kept_3y_vs_base_pct
    const range = high != null && Math.round(high) > Math.round(kept) ? `${Math.round(kept)}–${Math.round(high)}%` : `${Math.round(kept)}%`
    chips.push(chip(`A los 3 años suele conservar <strong>${range}</strong> de su precio 0 km`))
  }
  if (entry.new_today) chips.push(chip(`Un 0 km hoy cuesta <strong>${usd.format(entry.new_today)}</strong>`))
  chips.push(chip(`<strong>${entry.listings}</strong> publicados hoy`))
  $('chips').replaceChildren(...chips)

  renderChart(entry, km, year)
  renderSimilar(entry, year, km, mid)
}

function renderChart(entry, km, selectedYear) {
  const points = entry.years.map((y) => ({ year: y, ...estimate(entry, y, km) }))
  const labels = points.map((p) => p.year)
  const config = {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Máximo probable', data: points.map((p) => p.high), borderWidth: 0, pointRadius: 0, fill: '+1', backgroundColor: 'rgba(36,87,245,0.12)' },
        { label: 'Mínimo probable', data: points.map((p) => p.low), borderWidth: 0, pointRadius: 0, fill: false },
        {
          label: 'Precio estimado', data: points.map((p) => p.mid), borderColor: '#2457f5', borderWidth: 2.5, tension: 0.25,
          pointRadius: labels.map((y) => (y === selectedYear ? 6 : 0)), pointBackgroundColor: '#2457f5',
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${usd.format(Math.round(ctx.parsed.y / 10) * 10)}` } },
      },
      scales: { y: { ticks: { callback: (v) => usd.format(v) } } },
    },
  }
  if (chart) chart.destroy()
  chart = new Chart($('chart'), config)
}

function renderSimilar(entry, year, km, mid) {
  const close = entry.cars
    .filter(([y]) => Math.abs(y - year) <= 1)
    .sort((a, b) => Math.abs((a[1] ?? km) - km) - Math.abs((b[1] ?? km) - km))
    .slice(0, 6)
  $('similar-caption').textContent = close.length
    ? `${entry.brand} ${entry.model} de ${year - 1} a ${year + 1}, ordenados por kilometraje parecido.`
    : `No hay ${entry.brand} ${entry.model} de ${year - 1} a ${year + 1} publicados ahora.`
  $('similar').replaceChildren(...close.map(([y, k, price, dealer, url]) => {
    const li = document.createElement('li')
    const cheap = k != null && price < mid * 0.93
    li.innerHTML = `
      <span><strong>${escapeHtml(entry.model)} ${y}</strong> · ${k == null ? 'km sin dato' : `${num.format(k)} km`}
        ${cheap ? '<span class="tag cheap">Debajo del estimado</span>' : ''}</span>
      <span class="p">${usd.format(price)}</span>
      <span class="meta">${escapeHtml(dealer)}</span>
      <span class="meta" style="text-align:right">${safeUrl(url) ? `<a href="${safeUrl(url)}" target="_blank" rel="noopener noreferrer">Ver aviso</a>` : ''}</span>`
    return li
  }))
}

function renderStatic() {
  $('stat-listings').textContent = num.format(data.listings)
  $('stat-dealers').textContent = data.dealers
  $('stat-date').textContent = new Date(`${data.generated}T12:00:00`).toLocaleDateString('es-UY', { day: 'numeric', month: 'long', year: 'numeric' })
  $('q-mape').textContent = `${pct(data.quality.mape_pct)}%`
  $('q-raw').textContent = `${Math.round(data.quality.interval_raw_coverage_pct)}%`
  $('q-cov').textContent = `${Math.round(data.quality.interval_coverage_pct)}%`
  $('ev').replaceChildren(...data.electrified.map((e) => {
    const div = document.createElement('div')
    div.innerHTML = `<div class="big">${e.listings}</div><strong>${e.fuel === 'Eléctrico' ? 'Eléctricos' : 'Híbridos'}</strong>
      <span class="muted" style="display:block">${pct(e.share_pct)}% del stock · mediana ${usd.format(e.median_price)}</span>
      <span class="muted" style="display:block">${escapeHtml(e.top_brands)}</span>`
    return div
  }))
}

// The weekly GitHub Action commits a fresh data.json; reading it from the repo keeps the
// site current without redeploying. The copy shipped with the site is the fallback.
const LIVE_DATA = 'https://raw.githubusercontent.com/JoaquinRSC/vidriera-insights/main/web/data.json'

async function loadData() {
  try {
    const response = await fetch(LIVE_DATA, { cache: 'no-cache' })
    if (response.ok) return await response.json()
  } catch { /* offline or GitHub unavailable: use the bundled copy */ }
  return (await fetch('data.json')).json()
}

async function init() {
  data = await loadData()
  renderStatic()
  const brands = [...new Set(data.models.map((m) => m.brand))]
  fillSelect($('brand'), brands, 'Chevrolet')
  fillSelect($('model'), modelsOf($('brand').value).map((m) => m.model), 'Onix')
  onModel()
  setKm(60000)
  render()
  $('brand').addEventListener('change', onBrand)
  $('model').addEventListener('change', onModel)
  $('year').addEventListener('change', render)
  $('km').addEventListener('input', () => { $('km-number').value = $('km').value; render() })
  $('km-number').addEventListener('change', () => { setKm(Math.max(0, Number($('km-number').value) || 0)); render() })
}

init()
