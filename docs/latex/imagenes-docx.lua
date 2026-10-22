-- Word necesita PNG; el PDF principal conserva el logo vectorial.
function Image(el)
  if el.src == 'marca/cuc-logo-vector.pdf' then
    el.src = 'marca/cuc-logo.png'
  end
  el.src = el.src:gsub('%.pdf$', '.png')
  return el
end
