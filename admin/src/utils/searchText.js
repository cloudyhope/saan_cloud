// Persian-friendly matching for the header search: Arabic letter forms, ZWNJ and digit scripts must not cause misses.
export function normalize(value) {
  return String(value || '').toLowerCase()
    .replace(/ي/g, 'ی').replace(/ك/g, 'ک').replace(/[‌ـ]/g, '')
    .replace(/[۰-۹]/g, (d) => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, (d) => '٠١٢٣٤٥٦٧٨٩'.indexOf(d))
    .replace(/\s+/g, ' ').trim();
}

// Entries are { title, trail }. Every word of the query must appear in the title or its group;
// a title that starts with the first word ranks above one that merely contains it, then menu order.
export function rankEntries(entries, query, limit = 8) {
  const text = normalize(query);
  if (!text) return [];
  const tokens = text.split(' ');
  return entries
    .map((entry, order) => {
      const head = normalize(entry.title);
      const haystack = normalize([entry.title, ...(entry.trail || [])].join(' '));
      return { entry, order, hit: tokens.every((token) => haystack.includes(token)), score: head.startsWith(tokens[0]) ? 3 : head.includes(tokens[0]) ? 2 : 1 };
    })
    .filter((row) => row.hit)
    .sort((a, b) => b.score - a.score || a.order - b.order)
    .slice(0, limit)
    .map((row) => row.entry);
}

// "5000006", "۵۰۰۰۰۰۶" -> 5000006; anything else -> null.
export function visitNumber(query) {
  const text = normalize(query);
  return /^\d{1,9}$/.test(text) ? Number(text) : null;
}
