#let init(doc) = [
  #set heading(
    numbering: (..nums) => {
      let level = nums.pos().len()
      let n = nums.pos().last()
      if level == 1 {
        numbering("一、", n)
      } else if level == 2 {
        numbering("(一)", n)
      } else if level == 3 {
        numbering("1.", n)
      } else {
        numbering("(1)", n)
      }
    }
  )
  #set page(
    paper: "a4",
    numbering: "1"
  )
  #set text(
    font: ("Times New Roman", "DFKai-SB"),
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
  #show heading: set block(above: 1.5em, below: 1em)
  #show heading: set text(weight: "bold")
  #doc
]
