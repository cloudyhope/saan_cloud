// Shared photo preparation for visit and survey uploads: resize, compress and locate.
import Compressor from 'compressorjs';

const MAX_SIDE = 1920;

export function shrinkImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      const scale = Math.min(1, MAX_SIDE / Math.max(image.width, image.height));
      const canvas = document.createElement('canvas');
      canvas.width = Math.round(image.width * scale);
      canvas.height = Math.round(image.height * scale);
      canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(blob => {
        if (!blob) { reject(new Error('process')); return; }
        new Compressor(blob, { quality: 0.7, success: resolve, error: () => resolve(blob) });
      }, 'image/webp', 0.75);
    };
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error('read')); };
    image.src = url;
  });
}

// Browsers without WebP encoding fall back to PNG; keep the file name consistent with the content.
export function uploadName(file, blob) {
  const extension = blob.type === 'image/webp' ? 'webp' : blob.type === 'image/jpeg' ? 'jpg' : 'png';
  return (file.name || 'photo').replace(/\.[^/.]+$/, '') + '.' + extension;
}

export function locate() {
  if (!navigator.geolocation) return Promise.resolve({ latitude: null, longitude: null });
  return new Promise(resolve => navigator.geolocation.getCurrentPosition(
    position => resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude }),
    () => resolve({ latitude: null, longitude: null }), { timeout: 6000, maximumAge: 60000 }));
}
