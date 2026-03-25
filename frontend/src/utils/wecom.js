let wxSdkLoaded = false

export function loadWxScript() {
  return new Promise((resolve, reject) => {
    if (window.wx && wxSdkLoaded) {
      resolve()
      return
    }
    const script = document.createElement('script')
    script.src = 'https://res.wx.qq.com/open/js/jweixin-1.6.0.js'
    script.onload = () => {
      wxSdkLoaded = true
      resolve()
    }
    script.onerror = () => reject(new Error('Failed to load WeChat JS-SDK'))
    document.head.appendChild(script)
  })
}

export async function initWxConfig(config) {
  await loadWxScript()
  return new Promise((resolve, reject) => {
    wx.config({
      debug: false,
      appId: config.appId,
      timestamp: config.timestamp,
      nonceStr: config.nonceStr,
      signature: config.signature,
      jsApiList: [
        'chooseImage',
        'getLocation',
        'openLocation',
        'scanQRCode',
        'getNetworkType'
      ]
    })
    wx.ready(() => resolve())
    wx.error((err) => reject(err))
  })
}
