#let init(doc) = [
  #set heading(numbering: "1.1.1")
  #set page(
    paper: "a4",
    numbering: "1"
  )
  #set text(
    font: ("Times New Roman"), // "DFKai-SB"
    size: 12pt,
  )
  #set par(
    justify: true,
    leading: 1.2em,
    first-line-indent: 2em
  )
  #show strong: it => { // Chinese bold font fix
    show regex("\p{Han}+"): text.with(stroke: 0.3pt)
    it
  }
  #show figure: set block(breakable: true)
  #show figure.caption: set text(size: 10pt)
  #show figure.where(kind: table): set figure.caption(position: top)
  #show figure.where(kind: image): set figure.caption(position: bottom)
  #show heading: set block(above: 1.5em, below: 1em)
  #show heading: set text(weight: "bold")
  #doc
]

#let toc(doc) = [
  #set heading(numbering: "1.1.1")
  #show outline.entry: set outline.entry(fill: repeat([. ]))
  
  #outline(
    title: [Table of Contents],
    indent: auto
  )
  #pagebreak()
  #doc
]