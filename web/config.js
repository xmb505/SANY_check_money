// 配置文件 - 为动态加载设计
window.DYNAMIC_CONFIG = {
    // API服务器地址和端口
    API_BASE_URL: 'https://check_api.your_mysql_host',
    
    // 请求超时时间(毫秒)
    API_TIMEOUT: 5000,
    
    // 默认数据量
    DEFAULT_DATA_COUNT: 20,
    
    // 默认数据模式
    // usage: 用量模式 (新total_reading - 旧total_reading)
    // cost: 用钱模式 (新remainingBalance - 旧remainingBalance)
    // total: 总量模式 (直接用读表数据)
    // balance: 余额模式 (直接显示remainingBalance)
    DEFAULT_MODE: 'balance',
    
    // 背景图片配置
    BACKGROUND_IMAGE_URL: 'https://s3.bmp.ovh/imgs/2025/06/24/a08d3969ca418f84.png',  // 背景图片URL，留空则不显示背景图片
    BACKGROUND_IMAGE_OPACITY: 0.4,  // 背景图片透明度，范围0-1，0为完全透明，1为完全不透明
    BACKGROUND_BLUR_RADIUS: 20,  // 背景图片模糊半径，单位px，0为不模糊
    
    // 容器透明度配置
    CONTAINER_OPACITY: 0.8,  // 容器透明度，范围0-1，0为完全不透明，1为完全透明
    
    // 网站favicon配置
    FAVICON_URL: 'https://littleskin.cn/avatar/112989?size=128'  // favicon URL，留空则使用默认favicon
};