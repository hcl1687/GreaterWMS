import dayjs from 'dayjs'

export function generateSku(supplier_id) {
  const hash = (+new Date).toString(36)
  return `S${supplier_id}G${hash}`
}

export function showLocalTime(utc) {
  if (!utc) {
    return ''
  }

  return dayjs(utc).format('YYYY-MM-DD HH:mm:ss') 
}
