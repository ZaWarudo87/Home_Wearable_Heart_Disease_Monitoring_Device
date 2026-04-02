#import "@preview/cetz:0.4.2"

#set page(width: auto, height: auto, margin: 1cm)
#set text(font: ("sans-serif"), size: 13pt)

#cetz.canvas({
  import cetz.draw: *

  // 設定共用的節點尺寸與顏色
  let box-w = 3
  let box-h = 1.2
  let c-red = rgb("#803a1e")
  let c-green = rgb("#2e7d32")
  let c-blue = rgb("#c23b7a")

  set-style(stroke: (thickness: 1pt, paint: black))

  // 自定義：繪製帶圓角的矩形文字框
  let draw-node(pos, text-content, name: none) = {
    let n = if name == none { text-content } else { name }
    rect(
      (rel: (-box-w/2, -box-h/2), to: pos),
      (rel: (box-w/2, box-h/2), to: pos),
      radius: 0.1,
      name: n,
      fill: white
    )
    content(pos, text-content)
  }

  // 自定義：繪製單一水平連線與文字
  let line-to-text(node-name, text-content, dy: 0) = {
     line((node-name + ".east"), (rel: (0.6, 0), to: node-name + ".east"), name: node-name + "-line")
     content((rel: (0.1, dy), to: node-name + "-line.end"), box(align(left)[#text-content]), anchor: "west")
  }

  // 自定義：繪製一對多的樹狀分支連線（完美對齊第一個選項）
  let tree-node(node-name, items, dy: 0.8, dx: 0.4) = {
     let n = items.len()
     let start-x = 0.4
     let origin = node-name + ".east"

     // 頂部連線 (直接對齊第一個項目)
     line(origin, (rel: (start-x + dx, 0), to: origin), name: node-name + "-top")
     content((rel: (0.1, 0), to: node-name + "-top.end"), box(align(left)[#items.at(0)]), anchor: "west")

     if n > 1 {
       let bot-y = -(n - 1) * dy
       // 垂直往下畫分支線
       line(
         (rel: (start-x, 0), to: origin),
         (rel: (start-x, bot-y), to: origin)
       )
       // 剩餘的子項目連線
       for i in range(1, n) {
         let y = -i * dy
         line(
           (rel: (start-x, y), to: origin),
           (rel: (start-x + dx, y), to: origin)
         )
         content(
           (rel: (start-x + dx + 0.1, y), to: origin),
           box(align(left)[#items.at(i)]),
           anchor: "west"
         )
       }
     }
  }

  // ==========================================
  // 背景虛線外框與標題區域
  // ==========================================

  // ESP32 區塊 (紅)
  rect((0.2, -0.7), (7.0, -7.2), stroke: (paint: c-red, thickness: 1.5pt), radius: 0.2)
  content((0.6, -1.3), text(fill: c-red, size: 1.4em, weight: "bold")[ESP32], anchor: "west")
  content((2.8, -1.3), text(fill: c-red, size: 1em)[wearable device], anchor: "west")

  // Raspberry Pi 區塊 (綠)
  rect((7.5, -0.7), (23.0, -7.2), stroke: (paint: c-green, thickness: 1.5pt), radius: 0.2)
  content((7.9, -1.3), text(fill: c-green, size: 1.4em, weight: "bold")[Raspberry Pi], anchor: "west")
  content((12.0, -1.3), text(fill: c-green, size: 1em)[backend], anchor: "west")

  // Frontend 區塊 (藍)
  rect((0.2, -7.6), (23.0, -15.1), stroke: (paint: c-blue, thickness: 1.5pt), radius: 0.2)
  content((0.6, -8.2), text(fill: c-blue, size: 1.4em, weight: "bold")[Frontend], anchor: "west")
  content((3.5, -8.3), text(fill: c-blue, size: 1em)[HTML web app], anchor: "west")


  // ==========================================
  // ESP32 內部節點
  // ==========================================
  draw-node((2.2, -3.0), [AD8232], name: "ad")
  line-to-text("ad", [ECG])

  draw-node((2.2, -5.3), [Wi-Fi], name: "wifi")
  line-to-text("wifi", [send data \ via HTTP, \ WebSocket])


  // ==========================================
  // Raspberry Pi 內部節點
  // ==========================================
  draw-node((9.5, -2.5), [SQL], name: "sql")
  line-to-text("sql", [user health data])

  draw-node((9.5, -4.3), [processing], name: "processing")
  line-to-text("processing", [raw data \ filtering, MLP, \ HR calculation])

  draw-node((17.0, -2.5), [REST API], name: "rest")
  line-to-text("rest", [health data, \ data from the \ user and ESP32])

  draw-node((17.0, -4.3), [WebSocket], name: "ws2")
  line-to-text("ws2", [realtime ECG, \ data from ESP32])

  draw-node((9.5, -6.1), [requests], name: "requests")
  line-to-text("requests", [self-hosted Taide LLM API])


  // ==========================================
  // Frontend 內部節點
  // ==========================================
  // --- 第 1 行 ---
  draw-node((2.2, -9.5), [overview], name: "overview")
  tree-node("overview", ([resting BP], [average HR], [max HR], [ST slope], [Resting ECG], [AF Detection], [AI suggestion]))

  // --- 第 2 行 ---
  draw-node((10.5, -9.5), [resting BP], name: "rbp1")
  tree-node("rbp1", ([7 days], [30 days]))

  draw-node((10.5, -11.5), [HR (1 min)], name: "hr1")
  tree-node("hr1", ([1 hr], [6 hr]))

  draw-node((10.5, -13.5), [HR (30 min)], name: "hr30")
  tree-node("hr30", ([24 hr], [7 days]))

  // --- 第 3 行 ---
  draw-node((17.8, -8.8), [risk evaluate], name: "risk")
  tree-node("risk", ([risk score], [risk level]))

  draw-node((17.8, -10.8), [realtime ECG], name: "rt")
  tree-node("rt", ([waveform], [heart rate]))

  draw-node((17.8, -12.8), [health data], name: "hd")
  tree-node("hd", ([resting BP], [cholesterol], [fasting BS]))
})