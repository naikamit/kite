# 📱 PWA Installation Guide - Kite Trading Coach

Your web app is now a **Progressive Web App (PWA)**! Users can install it on Android (and iOS) like a native app.

---

## ✅ What Was Added

### 1. **PWA Manifest** (`/static/manifest.json`)
- App name, icons, colors, display mode
- Defines how the app appears when installed

### 2. **Service Worker** (`/static/service-worker.js`)
- Offline caching
- Background sync (for future use)
- Push notifications (ready for future use)

### 3. **App Icons** (`/static/icons/`)
- 11 icon sizes (16x16 to 512x512)
- Placeholder "K" logo (replace with your custom logo)

### 4. **Install Prompt** (in `app.js`)
- "Install App" button appears in header
- One-click installation

### 5. **PWA Meta Tags** (in `dashboard.html`)
- Mobile-friendly viewport
- Theme color, app icons
- iOS compatibility

---

## 📲 How Users Install the App

### **Android (Chrome/Edge)**

1. **Visit your website** on mobile Chrome
2. **Look for "Install App" button** in header (or browser prompt)
3. **Click "Install"**
4. **App appears on home screen** ✓

**OR** via Chrome menu:
- Chrome menu (⋮) → "Add to Home screen"

### **iOS (Safari)**

1. **Visit your website** on mobile Safari
2. **Tap Share button** (⬆️)
3. **Select "Add to Home Screen"**
4. **Tap "Add"**
5. **App appears on home screen** ✓

### **Desktop (Chrome/Edge)**

1. **Visit your website** on Chrome/Edge
2. **Click "Install App" button** in header
   - Or look for install icon in address bar (⊕)
3. **Click "Install"**
4. **App opens in own window** ✓

---

## 🎨 Customizing Your PWA

### **Replace Icons**

Option 1: **Use online generator** (easiest)
```bash
1. Visit: https://www.pwabuilder.com/imageGenerator
2. Upload your 512x512 logo
3. Download generated icons
4. Replace files in static/icons/
```

Option 2: **Run icon generator again**
```bash
# Edit generate_icons.py to use your logo
python generate_icons.py
```

Option 3: **Manually create**
- Create PNG files for each size in `/static/icons/`
- Required sizes: 16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512

### **Change App Name**

Edit `/static/manifest.json`:
```json
{
  "name": "Your App Name",
  "short_name": "Short Name",
  "description": "Your description"
}
```

### **Change Theme Color**

Edit `/static/manifest.json`:
```json
{
  "theme_color": "#1a73e8",  // Header color
  "background_color": "#ffffff"  // Splash screen color
}
```

And in `/templates/dashboard.html`:
```html
<meta name="theme-color" content="#1a73e8">
```

---

## 🚀 Testing Your PWA

### **Chrome DevTools**

1. **Open DevTools** (F12)
2. **Go to Application tab**
3. **Check "Manifest"** - should show your app details
4. **Check "Service Workers"** - should be "activated and running"
5. **Lighthouse** → "Progressive Web App" → "Generate report"

### **Mobile Testing**

Use Chrome Remote Debugging:
```bash
1. Connect Android device via USB
2. Enable USB Debugging on phone
3. Chrome → chrome://inspect
4. Test on real device
```

### **PWA Requirements Checklist**

✅ HTTPS (required for PWA)
✅ Valid manifest.json
✅ Service worker registered
✅ Icons (at least 192x192 and 512x512)
✅ Responsive design
✅ Works offline (basic caching)

---

## 🔧 Features Included

### **Offline Support**
- Static assets cached (CSS, JS, icons)
- API responses cached for offline viewing
- Fallback to cache when network fails

### **Install Prompt**
- Automatic "Install App" button
- Respects user's install/dismiss choice
- Tracks installation success

### **Online/Offline Detection**
- Shows toast when connection lost/restored
- Graceful degradation of features

### **Future Features (Ready to Implement)**

📋 **Background Sync**
```javascript
// Sync trades when back online
navigator.serviceWorker.ready.then(registration => {
  registration.sync.register('sync-trades');
});
```

🔔 **Push Notifications**
```javascript
// Request notification permission
Notification.requestPermission().then(permission => {
  if (permission === 'granted') {
    // Subscribe to push notifications
  }
});
```

---

## 📊 Analytics & Monitoring

### **Track PWA Installs**

Add to your analytics:
```javascript
window.addEventListener('appinstalled', () => {
  // Track in Google Analytics, etc.
  gtag('event', 'pwa_install');
});
```

### **Monitor Service Worker**

Check service worker status:
```javascript
navigator.serviceWorker.ready.then(registration => {
  console.log('Service Worker status:', registration.active.state);
});
```

---

## 🐛 Troubleshooting

### **Install button doesn't appear**

**Causes:**
- Not served over HTTPS
- Manifest.json not loading
- Service worker not registered

**Fix:**
```bash
# Check console for errors (F12)
# Verify HTTPS is enabled
# Check manifest at: /static/manifest.json
# Check service worker at: /static/service-worker.js
```

### **Icons not showing**

**Causes:**
- Icons not generated
- Wrong file paths in manifest.json

**Fix:**
```bash
# Regenerate icons
python generate_icons.py

# Verify paths
ls static/icons/
```

### **Service worker not updating**

**Causes:**
- Browser caching old version
- Service worker not calling skipWaiting()

**Fix:**
```bash
# Hard refresh (Ctrl + Shift + R)
# Or clear service workers in DevTools
# Application → Service Workers → Unregister
```

---

## 🌐 Deployment Checklist

Before deploying PWA:

- [ ] HTTPS enabled on your server
- [ ] Custom icons generated
- [ ] Manifest.json customized (name, colors)
- [ ] Tested on real mobile device
- [ ] Lighthouse PWA score > 90
- [ ] Service worker registered successfully
- [ ] Install prompt tested

---

## 📚 Resources

- **PWA Builder**: https://www.pwabuilder.com/
- **Icon Generator**: https://realfavicongenerator.net/
- **PWA Checklist**: https://web.dev/pwa-checklist/
- **Workbox** (advanced service workers): https://developers.google.com/web/tools/workbox

---

## 🎯 Next Steps

**Immediate:**
1. Test PWA on your Android device
2. Replace placeholder icons with your logo
3. Customize app name and colors

**Later:**
1. Add push notifications for trade alerts
2. Implement background sync for offline trades
3. Add app shortcuts (quick actions)
4. Create splash screen
5. Submit to Google Play Store (via TWA)

---

## 📞 Support

**Issues?**
- Check browser console for errors
- Test in incognito/private mode
- Use Chrome DevTools Lighthouse
- Check PWA requirements checklist above

**Success?** 🎉
- Your app is now installable on all devices!
- Works offline automatically
- Updates automatically when you deploy

---

**Built with**: FastAPI + Vanilla JS + PWA APIs
**Compatible with**: Chrome, Edge, Safari, Firefox (partial)
