export function generateSku(supplier_id) {
  const hash = (+new Date).toString(36)
  return `S${supplier_id}G${hash}`
}
