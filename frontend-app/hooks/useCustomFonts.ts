import { useFonts } from 'expo-font';

export const useCustomFonts = () => {
  const [fontsLoaded] = useFonts({
    'ChelaOne-Regular': 'https://fonts.googleapis.com/css2?family=Chela+One&display=swap',
  });

  return fontsLoaded;
};

// For web platform, inject the Google Fonts CSS
if (typeof document !== 'undefined') {
  const link1 = document.createElement('link');
  link1.rel = 'preconnect';
  link1.href = 'https://fonts.googleapis.com';
  document.head.appendChild(link1);

  const link2 = document.createElement('link');
  link2.rel = 'preconnect';
  link2.href = 'https://fonts.gstatic.com';
  link2.crossOrigin = 'anonymous';
  document.head.appendChild(link2);

  const link3 = document.createElement('link');
  link3.rel = 'stylesheet';
  link3.href = 'https://fonts.googleapis.com/css2?family=Chela+One&display=swap';
  document.head.appendChild(link3);
}