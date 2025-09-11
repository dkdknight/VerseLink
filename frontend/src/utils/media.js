export const getMediaUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  const base = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  return `${base}${url}`;
};