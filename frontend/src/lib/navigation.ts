export const totalPages = 4;

export function nextPage(page: number): number | null {
  return page >= totalPages ? null : page + 1;
}

export function prevPage(page: number): number | null {
  return page <= 1 ? null : page - 1;
}