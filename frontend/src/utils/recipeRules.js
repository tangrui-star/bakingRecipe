/**
 * 配方计算规则 A1~A21
 * 每条规则定义：关联商品、批次数计算方式、材料列表
 */

// 商品名称关键词匹配（模糊匹配，避免因括号/空格差异导致匹配失败）
export const matchProduct = (productName, keyword) => {
  if (!productName || !keyword) return false
  return productName.includes(keyword)
}

// 从汇总数据中查找商品数量
export const findQty = (summaryList, keyword) => {
  const item = summaryList.find(s => matchProduct(s['商品'], keyword))
  return item ? (item['数量'] || 0) : 0
}

/**
 * 执行所有配方计算
 * @param {Array} summaryList - 商品数量汇总结果
 * @returns {Array} 配方计算结果列表
 */
export const calcRecipes = (summaryList) => {
  const results = []

  const add = (id, name, formulaNumber, materials) => {
    if (formulaNumber <= 0) return
    const row = { formulaId: id, formulaName: name, formulaNumber }
    materials.forEach((m, i) => {
      row[`subitem${i + 1}`] = m.name
      row[`subitem${i + 1}Weight`] = m.weight
    })
    // 补全空材料位
    for (let i = materials.length + 1; i <= 7; i++) {
      row[`subitem${i}`] = ''
      row[`subitem${i}Weight`] = ''
    }
    results.push(row)
  }

  // A1 番茄肉松贝果
  const a1 = findQty(summaryList, '芝士番茄全麦肉松贝果')
  if (a1 > 0) {
    const n = Math.ceil(a1 / 3)
    add('A1', '番茄肉松贝果', n, [
      { name: '肉松', weight: `${75 * n}g` },
      { name: '芝士', weight: `${30 * n}g` },
      { name: '番茄', weight: `${15 * n}g` },
      { name: '辣椒', weight: `${5 * n}g` },
    ])
  }

  // A2 咸蛋黄
  const a2a = findQty(summaryList, '全麦咸蛋黄肉松碱水')
  const a2b = findQty(summaryList, '艾草咸蛋黄肉松贝果')
  const a2total = a2a + a2b
  if (a2total > 0) {
    add('A2', '咸蛋黄', a2total, [
      { name: '蛋', weight: `${Math.floor(a2total / 4)}个` },
      { name: '肉松', weight: `${35 * a2total}g` },
    ])
  }

  // A3 章鱼烧
  const a3 = findQty(summaryList, '章鱼烧贝果')
  if (a3 > 0) {
    add('A3', '章鱼烧', a3, [
      { name: '肠', weight: `${Math.round(a3 / 4)}个` },
      { name: '肉松', weight: `${30 * a3}g` },
      { name: '海苔', weight: `${5 * a3}g` },
      { name: '酱', weight: `${2.5 * a3}g` },
    ])
  }

  // A4 鸡枞菌
  const a4 = findQty(summaryList, '低油无糖鸡枞菌恰巴塔')
  if (a4 > 0) {
    const n = Math.ceil(a4 / 3) + 1
    add('A4', '鸡枞菌', n, [
      { name: '面', weight: `${300 * n}g` },
      { name: '水', weight: `${250 * n}g` },
      { name: '油', weight: `${20 * n}g` },
      { name: '鸡枞菌', weight: `${50 * n}g` },
      { name: '酵母粉', weight: `${1 * n}g` },
      { name: '盐', weight: `${4 * n}g` },
    ])
  }

  // A5 鸡肉欧包（面团）
  const a5 = findQty(summaryList, '无油糖葱香鸡肉干乳酪丁欧包')
  if (a5 > 0) {
    const n = (a5 + 1) / 2
    add('A5', '鸡肉欧包', n, [
      { name: '面', weight: `${500 * n}g` },
      { name: '洋葱', weight: `${10 * n}g` },
      { name: '叶子', weight: `${2 * n}g` },
      { name: '水', weight: `${320 * n}g` },
      { name: '酵母粉', weight: `${2 * n}g` },
      { name: '盐', weight: `${10 * n}g` },
    ])
    // A6 鸡肉欧包后加
    add('A6', '鸡肉欧包后加', n, [
      { name: '鸡肉', weight: `${50 * n}g` },
      { name: '乳酪丁', weight: `${20 * n}g` },
    ])
  }

  // A7 青提欧包（面团）
  const a7 = findQty(summaryList, '无油低糖酒渍青提茉莉欧包')
  if (a7 > 0) {
    const n = (a7 + 1) / 2
    add('A7', '青提欧包', n, [
      { name: '面', weight: `${500 * n}g` },
      { name: '酱', weight: `${50 * n}g` },
      { name: '茉莉粉', weight: `${4 * n}g` },
      { name: '抹茶粉', weight: `${2 * n}g` },
      { name: '水', weight: `${290 * n}g` },
      { name: '酵母粉', weight: `${2 * n}g` },
      { name: '糖', weight: `${10 * n}g` },
    ])
    // A8 青提欧包后加
    add('A8', '青提欧包后加', n, [
      { name: '葡萄干', weight: `${50 * n}g` },
      { name: '花', weight: `${10 * n}g` },
    ])
  }

  // A9 曲奇
  // 美式大曲奇（全分类）- 排除特定商品，燕麦曲奇/2
  const cookieKeywords = ['美式大曲奇', '美式曲奇']
  const excludeKeywords = ['燕麦']
  let cookieTotal = 0
  summaryList.forEach(s => {
    const name = s['商品'] || ''
    const isMatch = cookieKeywords.some(k => name.includes(k))
    const isExclude = excludeKeywords.some(k => name.includes(k))
    if (isMatch && !isExclude) cookieTotal += (s['数量'] || 0)
  })
  const oatCookie = findQty(summaryList, '燕麦曲奇')
  const a9raw = cookieTotal + oatCookie / 2
  if (a9raw > 0) {
    const n = Math.ceil(a9raw / 6)
    add('A9', '曲奇', n, [
      { name: '鸡蛋', weight: `${n - 1}个` },
      { name: '油', weight: `${125 * n}g` },
      { name: '面', weight: `${215 * n}g` },
      { name: '糖', weight: `${50 * n}g` },
      { name: '泡打粉', weight: `${1 * n}g` },
    ])
  }

  // A10 燕麦片
  const a10a = findQty(summaryList, '每日可可黑巧坚果多多烤燕麦片小包')
  const a10b = findQty(summaryList, '无油黑巧可可坚果烤燕麦片')
  if (a10a > 0 || a10b > 0) {
    add('A10', '燕麦片', a10a + a10b, [
      { name: '燕麦片小包', weight: `${a10a}包` },
      { name: '燕麦片大包', weight: `${a10b}包` },
    ])
  }

  // A11 煮红豆
  const a11a = findQty(summaryList, '古早红豆肉松碱水')
  const a11b = findQty(summaryList, '抹茶红豆碱水')
  const a11total = a11a + a11b
  if (a11total > 0) {
    add('A11', '煮红豆', a11total, [
      { name: '红豆', weight: `${a11total * 15}g` },
    ])
  }

  // A13 黑芝麻粉
  const a13 = findQty(summaryList, '黑芝麻花生双拼贝果')
  if (a13 > 0) {
    const n = Math.ceil(a13 / 2)
    add('A13', '黑芝麻粉', n, [
      { name: '黑芝麻粉', weight: `${40 * n}g` },
      { name: '奶粉', weight: `${10 * n}g` },
      { name: '糖', weight: `${2 * n}g` },
    ])
  }

  // A14 花生（白）- 肉桂+可可
  const a14a = findQty(summaryList, '无油糖肉桂花生碱水')
  const a14b = findQty(summaryList, '全麦可可巧克力奇亚籽花生贝果')
  if (a14a > 0 || a14b > 0) {
    add('A14', '花生（白）肉桂可可', a14a + a14b, [
      { name: '肉桂花生', weight: `${50 * a14a}g` },
      { name: '肉桂粉', weight: `${3 * a14a}g` },
      { name: '糖(肉桂)', weight: `${2 * a14a}g` },
      { name: '可可花生', weight: `${50 * a14b}g` },
      { name: '可可粉', weight: `${2 * a14b}g` },
      { name: '糖(可可)', weight: `${2 * a14b}g` },
    ])
  }

  // A15 花生（白）- 黑芝麻+香蕉
  const a15a = findQty(summaryList, '黑芝麻花生双拼贝果')
  const a15b = findQty(summaryList, '香蕉布朗尼花生贝果')
  if (a15a > 0 || a15b > 0) {
    const peanutTotal = 25 * a15a + 50 * a15b
    add('A15', '花生（白）黑芝麻香蕉', a15a + a15b, [
      { name: '黑芝麻花生', weight: `${25 * a15a}g` },
      { name: '香蕉花生', weight: `${50 * a15b}g` },
      { name: '糖', weight: `${Math.ceil(peanutTotal / 25)}g` },
    ])
  }

  // A16 花生（粗）
  const a16a = findQty(summaryList, '全麦花生贝果')
  const a16b = findQty(summaryList, '海盐花生碱水包')
  const a16c = findQty(summaryList, '花生奇亚籽黑巧美式曲奇')
  if (a16a > 0 || a16b > 0 || a16c > 0) {
    add('A16', '花生（粗）', a16a + a16b, [
      { name: '花生', weight: `${50 * (a16a + a16b) + 30 * a16c}g` },
    ])
  }

  // A17 花生（细）
  const a17a = findQty(summaryList, '全麦花生坚果辣松贝果')
  const a17b = findQty(summaryList, '全麦花生坚果辣松碱水')
  const a17c = findQty(summaryList, '花生酱')
  if (a17a > 0 || a17b > 0 || a17c > 0) {
    add('A17', '花生（细）', a17a + a17b + a17c, [
      { name: '花生', weight: `${30 * (a17a + a17b) + 100 * a17c}g` },
      { name: '肉松', weight: `${20 * (a17a + a17b)}g` },
      { name: '花生酱', weight: `${a17c}瓶` },
    ])
  }

  // A18 腰果
  const a18a = findQty(summaryList, '无油糖椰香斑斓腰果贝果')
  const a18b = findQty(summaryList, '无油糖抹茶腰果碱水')
  const a21a = findQty(summaryList, '斑斓椰香奇亚籽腰果酱')
  const a21b = findQty(summaryList, '抹茶腰果酱')
  if (a18a > 0 || a18b > 0) {
    add('A18', '腰果', a18a + a18b, [
      { name: '腰果', weight: `${50 * (a18a + a18b) + (a21a + a21b) * 100}g` },
    ])
  }

  // A19 斑斓腰果贝果
  if (a18a > 0) {
    add('A19', '斑斓腰果贝果', a18a, [
      { name: '斑斓', weight: `${50 * a18a}g` },
      { name: '斑斓粉', weight: `${2 * a18a}g` },
      { name: '糖', weight: `${1 * a18a}g` },
      { name: '椰奶粉', weight: `${2 * a18a}g` },
    ])
  }

  // A20 抹茶腰果碱水
  if (a18b > 0) {
    add('A20', '抹茶腰果碱水', a18b, [
      { name: '抹茶', weight: `${50 * a18b}g` },
      { name: '抹茶粉', weight: `${2 * a18b}g` },
      { name: '糖', weight: `${1 * a18b}g` },
    ])
  }

  // A21 斑斓酱
  if (a21a > 0 || a21b > 0) {
    add('A21', '斑斓酱', a21a + a21b, [
      { name: '斑斓酱', weight: `${a21a}瓶` },
      { name: '抹茶腰果酱', weight: `${a21b}瓶` },
    ])
  }

  return results
}
