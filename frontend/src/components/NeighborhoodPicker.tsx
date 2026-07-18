import { useEffect, useRef, useState } from 'react'

interface Props {
  value: string
  options: string[]
  onChange: (value: string) => void
}

export function NeighborhoodPicker({ value, options, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const wrapRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  const filtered = options
    .filter((o) => o.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 60)

  function pick(name: string) {
    onChange(name)
    setQuery('')
    setOpen(false)
  }

  return (
    <div className="field" ref={wrapRef}>
      <input
        className="combo-input"
        placeholder="Neighborhood"
        value={open ? query : value}
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          setQuery(e.target.value)
          setActive(0)
          setOpen(true)
        }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') {
            e.preventDefault()
            setActive((a) => Math.min(a + 1, filtered.length - 1))
          } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setActive((a) => Math.max(a - 1, 0))
          } else if (e.key === 'Enter' && filtered[active]) {
            e.preventDefault()
            pick(filtered[active])
          } else if (e.key === 'Escape') {
            setOpen(false)
          }
        }}
      />
      {open && (
        <div className="combo-pop" role="listbox">
          {filtered.length === 0 && <div className="combo-empty">No matches</div>}
          {filtered.map((o, i) => (
            <button
              key={o}
              className={i === active ? 'active' : ''}
              onMouseEnter={() => setActive(i)}
              onClick={() => pick(o)}
              role="option"
              aria-selected={o === value}
            >
              {o}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
