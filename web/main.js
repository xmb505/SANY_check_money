// 全局变量
let CONFIG = {}; // 初始化为空对象，稍后动态加载
let currentDataCount = 5; // 默认值
let currentMode = 'usage'; // 默认值
let currentDeviceIds = [];
let deviceDataCache = {};

// 带超时的fetch函数
async function fetchWithTimeout(url, options = {}) {
    // 使用默认超时时间5000毫秒，如果配置已加载则使用配置的值
    const timeout = (CONFIG && CONFIG.API_TIMEOUT) ? CONFIG.API_TIMEOUT : 5000;
    
    const timeoutId = setTimeout(() => {
        console.error(`请求超时: ${url}`);
        throw new Error(`请求超时: ${url}`);
    }, timeout);

    try {
        const response = await fetch(url, options);
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

// 动态加载配置文件，避免缓存
function loadConfig() {
    return new Promise((resolve, reject) => {
        // 使用时间戳避免缓存
        const timestamp = Date.now();
        const script = document.createElement('script');
        script.src = `config.js?_t=${timestamp}`;
        
        script.onload = () => {
            // 确保DYNAMIC_CONFIG对象存在
            if (window.DYNAMIC_CONFIG) {
                CONFIG = window.DYNAMIC_CONFIG;
                
                // 设置默认值（如果配置中没有定义）
                if (CONFIG.DEFAULT_DATA_COUNT === undefined) CONFIG.DEFAULT_DATA_COUNT = 5;
                if (CONFIG.DEFAULT_MODE === undefined) CONFIG.DEFAULT_MODE = 'usage';
                if (CONFIG.API_TIMEOUT === undefined) CONFIG.API_TIMEOUT = 5000;
                if (CONFIG.API_BASE_URL === undefined) CONFIG.API_BASE_URL = 'http://localhost:8080';
                
                // 更新全局变量
                currentDataCount = CONFIG.DEFAULT_DATA_COUNT;
                currentMode = CONFIG.DEFAULT_MODE;
                
                resolve();
            } else {
                reject(new Error('配置文件加载失败'));
            }
        };
        
        script.onerror = () => {
            reject(new Error('配置文件加载失败'));
        };
        
        document.head.appendChild(script);
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 首先加载配置
    loadConfig()
        .then(() => {
            // 检查系统主题偏好
            checkSystemTheme();
            
            // 设置背景图片
            setBackgroudImage();
            
            // 设置favicon
            setFavicon();
            
            // 初始化选项卡
            initTabs();
            
            // 初始化数据量选择按钮
            initDataCountButtons();
            
            // 初始化模式按钮
            initModeButtons();
            
            // 初始化搜索功能
            initSearch();
            
            // 初始化图表模态框
            initModal();
            
            // 显示连接服务器提示
            const cardsContainer = document.getElementById('cards-container');
            cardsContainer.innerHTML = '<p>正在连接服务器，如果长时间没有反应，请联系管理员。</p>';
            
            // 加载首页数据
            loadFirstScreenData();
        })
        .catch(error => {
            console.error('配置加载失败:', error);
            // 使用默认配置继续执行
            currentDataCount = 5;
            currentMode = 'usage';
            
            // 检查系统主题偏好
            checkSystemTheme();
            
            // 设置背景图片
            setBackgroudImage();
            
            // 设置favicon
            setFavicon();
            
            // 初始化选项卡
            initTabs();
            
            // 初始化数据量选择按钮
            initDataCountButtons();
            
            // 初始化模式按钮
            initModeButtons();
            
            // 初始化搜索功能
            initSearch();
            
            // 初始化图表模态框
            initModal();
            
            // 显示连接服务器提示
            const cardsContainer = document.getElementById('cards-container');
            cardsContainer.innerHTML = '<p>正在连接服务器，如果长时间没有反应，请联系管理员。</p>';
            
            // 加载首页数据
            loadFirstScreenData();
        });
});

// 设置favicon
function setFavicon() {
    // 检查是否有配置favicon URL
    if (CONFIG && CONFIG.FAVICON_URL) {
        // 查找现有的favicon链接
        let favicon = document.querySelector('link[rel="icon"]');
        if (favicon) {
            // 更新现有favicon
            favicon.href = CONFIG.FAVICON_URL;
        } else {
            // 创建新的favicon链接
            favicon = document.createElement('link');
            favicon.rel = 'icon';
            favicon.href = CONFIG.FAVICON_URL;
            document.head.appendChild(favicon);
        }
    }
}

// 设置背景图片
function setBackgroudImage() {
    // 检查是否有配置背景图片URL
    if (CONFIG && CONFIG.BACKGROUND_IMAGE_URL) {
        document.body.style.backgroundImage = `url('${CONFIG.BACKGROUND_IMAGE_URL}')`;
        document.body.style.backgroundSize = 'cover';
        document.body.style.backgroundPosition = 'center';
        document.body.style.backgroundRepeat = 'no-repeat';
        document.body.style.backgroundAttachment = 'fixed';
        
        // 更新背景透明度
        updateBackgroundOpacity();
    }
    
    // 设置容器透明度
    setContainerOpacity();
}

// 设置容器透明度
function setContainerOpacity() {
    const container = document.querySelector('.container');
    if (container) {
        // 使用默认透明度0.8，如果配置已加载则使用配置的值
        const opacity = CONFIG && CONFIG.CONTAINER_OPACITY !== undefined ? 
            Math.max(0, Math.min(1, CONFIG.CONTAINER_OPACITY)) : 0.8;
        container.style.backgroundColor = `rgba(255, 255, 255, ${opacity})`;
        
        // 检查是否为暗色模式
        if (document.body.classList.contains('dark-mode')) {
            container.style.backgroundColor = `rgba(45, 45, 45, ${opacity})`;
        }
    }
}

// 检查系统主题偏好
function checkSystemTheme() {
    // 检查系统是否偏好暗色主题
    const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // 根据系统偏好设置主题
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
    
            // 监听系统主题变化
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                if (e.matches) {
                    document.body.classList.add('dark-mode');
                } else {
                    document.body.classList.remove('dark-mode');
                }
                // 主题变化时更新背景透明度
                if (CONFIG && CONFIG.BACKGROUND_IMAGE_URL) {
                    updateBackgroundOpacity();
                }
                // 主题变化时更新容器透明度
                setContainerOpacity();
            });
        }
}

// 更新背景图片透明度（处理主题切换）
function updateBackgroundOpacity() {
    // 使用默认值，如果配置已加载则使用配置的值
    const opacity = CONFIG && CONFIG.BACKGROUND_IMAGE_OPACITY !== undefined ? 
        Math.max(0, Math.min(1, CONFIG.BACKGROUND_IMAGE_OPACITY)) : 0.4;
    const blurRadius = CONFIG && CONFIG.BACKGROUND_BLUR_RADIUS !== undefined ? 
        Math.max(0, CONFIG.BACKGROUND_BLUR_RADIUS) : 10;
    
    // 移除现有的背景样式
    const existingStyles = document.querySelectorAll('style[data-bg-overlay]');
    existingStyles.forEach(style => style.remove());
    
    // 添加新的背景样式
    const style = document.createElement('style');
    style.setAttribute('data-bg-overlay', 'true');
    style.textContent = `
        body {
            background-color: ${document.body.classList.contains('dark-mode') ? '#1a1a1a' : '#f5f5f5'};
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('${CONFIG && CONFIG.BACKGROUND_IMAGE_URL ? CONFIG.BACKGROUND_IMAGE_URL : ''}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            opacity: 1;
            z-index: -2;
            pointer-events: none;
        }
        
        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: ${document.body.classList.contains('dark-mode') ? '#1a1a1a' : '#f5f5f5'};
            opacity: ${opacity};
            z-index: -1;
            pointer-events: none;
        }
        
        .container,
        .header,
        .tab-content,
        .main-content,
        .modal-content,
        .card {
            ${blurRadius > 0 ? `backdrop-filter: blur(${blurRadius}px);` : ''}
        }
        
        body.dark-mode .container,
        body.dark-mode .header,
        .tab-content,
        body.dark-mode .main-content,
        body.dark-mode .modal-content,
        body.dark-mode .card {
            ${blurRadius > 0 ? `backdrop-filter: blur(${blurRadius}px);` : ''}
        }
    `;
    document.head.appendChild(style);
}

// 初始化选项卡
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 移除所有选项卡的激活状态
            tabs.forEach(t => t.classList.remove('active'));
            
            // 为当前选项卡添加激活状态
            this.classList.add('active');
            
            // 显示对应的选项卡内容
            const tabName = this.getAttribute('data-tab');
            showTabContent(tabName);
        });
    });
}

// 显示选项卡内容
function showTabContent(tabName) {
    // 隐藏所有选项卡内容
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(pane => pane.classList.remove('active'));
    
    // 显示对应的选项卡内容
    const targetPane = document.getElementById(`${tabName}-pane`);
    if (targetPane) {
        targetPane.classList.add('active');
    }
}

// 初始化数据量选择按钮
function initDataCountButtons() {
    const countButtons = document.querySelectorAll('.count-btn');
    const customInput = document.getElementById('custom-count-input');
    const setCustomBtn = document.getElementById('set-custom-count');
    
    // 设置初始激活按钮
    updateActiveButton(currentDataCount);
    
    // 监听预设按钮点击
    countButtons.forEach(button => {
        button.addEventListener('click', function() {
            const count = parseInt(this.getAttribute('data-count'));
            currentDataCount = count;
            customInput.value = ''; // 清空自定义输入框
            
            // 更新激活按钮
            updateActiveButton(count);
            
            // 重新加载数据
            if (currentDeviceIds.length > 0) {
                reloadDeviceData();
            }
        });
    });
    
    // 监听自定义数量设置按钮
    setCustomBtn.addEventListener('click', function() {
        const customValue = parseInt(customInput.value);
        if (customValue && customValue > 0 && customValue <= 1000) {
            currentDataCount = customValue;
            
            // 更新激活按钮（如果没有匹配的预设按钮，则取消所有按钮的激活状态）
            updateActiveButton(customValue);
            
            // 重新加载数据
            if (currentDeviceIds.length > 0) {
                reloadDeviceData();
            }
        } else {
            alert('请输入1到1000之间的有效数字');
        }
    });
    
    // 监听回车键
    customInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            setCustomBtn.click();
        }
    });
}

// 更新激活按钮
function updateActiveButton(count) {
    const countButtons = document.querySelectorAll('.count-btn');
    
    // 移除所有按钮的激活状态
    countButtons.forEach(btn => btn.classList.remove('active'));
    
    // 查找匹配的按钮并激活
    const matchingButton = Array.from(countButtons).find(btn => 
        parseInt(btn.getAttribute('data-count')) === count
    );
    
    if (matchingButton) {
        matchingButton.classList.add('active');
    }
}

// 初始化模式按钮
function initModeButtons() {
    const modeButtons = document.querySelectorAll('.mode-btn');
    modeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 移除所有模式按钮的激活状态
            modeButtons.forEach(btn => btn.classList.remove('active'));
            
            // 为当前按钮添加激活状态
            this.classList.add('active');
            
            // 更新当前模式
            currentMode = this.getAttribute('data-mode');
            
            // 重新渲染卡片数据
            renderAllCards();
        });
    });
}

// 初始化搜索功能
function initSearch() {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    
    // 监听搜索按钮点击
    searchBtn.addEventListener('click', function() {
        performSearch();
    });
    
    // 监听回车键
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// 执行搜索
function performSearch() {
    const keyword = document.getElementById('search-input').value.trim();
    
    if (keyword) {
        // 发送搜索请求
        searchDevices(keyword);
    }
}

// 初始化图表模态框
function initModal() {
    const modals = document.querySelectorAll('.modal');
    const closeBtns = document.querySelectorAll('.close');
    
    // 关闭模态框
    closeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            modal.style.display = 'none';
        });
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
}

// 加载首页数据
async function loadFirstScreenData() {
    try {
        // 使用默认API地址，如果配置已加载则使用配置的地址
        const apiUrl = CONFIG && CONFIG.API_BASE_URL ? CONFIG.API_BASE_URL : 'http://localhost:8080';
        const response = await fetchWithTimeout(`${apiUrl}/?mode=first_screen`);
        const data = await response.json();
        
        if (data.code === "200") {
            // 保存设备ID列表
            currentDeviceIds = data.device_ids || [];
            
            // 加载每个设备的详细数据
            await loadDeviceDataForIds(currentDeviceIds, data.total_num);
        } else {
            console.error('加载首页数据失败:', data);
        }
    } catch (error) {
        console.error('加载首页数据时出错:', error);
    }
}

// 为设备ID列表加载数据
async function loadDeviceDataForIds(deviceIds, totalNum = deviceIds.length) {
    const cardsContainer = document.getElementById('cards-container');
    cardsContainer.innerHTML = `<p>数据查询中(0/${totalNum})...</p>`;
    
    // 清空缓存
    deviceDataCache = {};
    
    // 串行请求每个设备的数据
    let loadedCount = 0;
    for (const deviceId of deviceIds) {
        try {
            await loadDeviceData(deviceId);
            loadedCount++;
            // 更新进度显示
            cardsContainer.innerHTML = `<p>数据查询中(${loadedCount}/${totalNum})...</p>`;
        } catch (error) {
            console.error(`加载设备 ${deviceId} 数据时出错:`, error);
            loadedCount++;
            // 更新进度显示
            cardsContainer.innerHTML = `<p>数据查询中(${loadedCount}/${totalNum})...</p>`;
        }
    }
    
    // 渲染所有卡片
    renderAllCards();
}

// 加载单个设备的数据
async function loadDeviceData(deviceId) {
    // 使用默认API地址，如果配置已加载则使用配置的地址
    const apiUrl = CONFIG && CONFIG.API_BASE_URL ? CONFIG.API_BASE_URL : 'http://localhost:8080';
    const response = await fetchWithTimeout(`${apiUrl}/?mode=check&device_id=${deviceId}&data_num=${currentDataCount}`);
    const data = await response.json();
    
    if (data.code === 200) {
        // 保存到缓存
        deviceDataCache[deviceId] = data;
    } else {
        console.error(`获取设备 ${deviceId} 数据失败:`, data);
    }
}

// 重新加载设备数据
async function reloadDeviceData() {
    if (currentDeviceIds.length > 0) {
        await loadDeviceDataForIds(currentDeviceIds);
    }
}

// 渲染所有卡片
function renderAllCards() {
    const cardsContainer = document.getElementById('cards-container');
    cardsContainer.innerHTML = '';
    
    // 为每个设备创建卡片
    currentDeviceIds.forEach(deviceId => {
        const deviceData = deviceDataCache[deviceId];
        if (deviceData) {
            const card = createDeviceCard(deviceData);
            cardsContainer.appendChild(card);
        }
    });
}

// 创建设备卡片
function createDeviceCard(deviceData) {
    const card = document.createElement('div');
    card.className = 'card';
    
    // 判断设备类型
    const isElectric = deviceData.equipmentType === '0' || deviceData.equipmentType === 0;
    const deviceType = isElectric ? '电表' : '水表';
    const typeClass = isElectric ? 'electric' : 'water';
    
    // 计算显示的数据
    const displayData = calculateDisplayData(deviceData.rows);
    
    // 构建卡片HTML
    card.innerHTML = `
        <div class="card-header">
            <div class="card-title">${deviceData.equipmentName}</div>
            <div class="card-badges">
                <div class="card-type ${typeClass}">${deviceType}</div>
                <div class="status-indicator ${deviceData.status === '1' || deviceData.status === 1 ? 'status-on' : 'status-off'}"></div>
            </div>
        </div>
        <div class="chart-container">
            <canvas class="mini-chart" data-device-id="${deviceData.device_id}"></canvas>
        </div>
        <button class="toggle-details-btn" data-device-id="${deviceData.device_id}">查看详细信息</button>
    `;
    
    // 添加查看详细信息按钮事件监听器
    const toggleBtn = card.querySelector('.toggle-details-btn');
    
    toggleBtn.addEventListener('click', function() {
        showDetailedInfo(deviceData);
    });
    
    // 初始时创建迷你图表，并添加点击事件
    setTimeout(() => {
        createMiniChart(deviceData, card);
        const miniChart = card.querySelector('.mini-chart');
        miniChart.addEventListener('click', function() {
            showChart(deviceData);
        });
    }, 100);
    
    return card;
}

// 计算显示的数据
function calculateDisplayData(rows) {
    if (!rows || rows.length === 0) {
        return [];
    }
    
    switch (currentMode) {
        case 'usage':
            // 用量模式: 新total_reading - 旧total_reading
            // 只计算到倒数第二个数据，避免最后一个显示N/A
            const usageData = [];
            for (let i = 0; i < rows.length - 1; i++) {
                const currentReading = parseFloat(rows[i].total_reading);
                const previousReading = parseFloat(rows[i + 1].total_reading);
                const usage = (currentReading - previousReading).toFixed(2);
                
                usageData.push({
                    time: rows[i].read_time,
                    value: usage
                });
            }
            return usageData;
            
        case 'cost':
            // 用钱模式: 新remainingBalance - 旧remainingBalance
            // 只计算到倒数第二个数据，避免最后一个显示N/A
            // 只有负数才表示消耗，正数表示充值
            const costData = [];
            for (let i = 0; i < rows.length - 1; i++) {
                const currentBalance = parseFloat(rows[i].remainingBalance);
                const previousBalance = parseFloat(rows[i + 1].remainingBalance);
                const diff = currentBalance - previousBalance;
                
                let value;
                if (diff < 0) {
                    value = `消耗: ${Math.abs(diff).toFixed(2)}`;
                } else if (diff > 0) {
                    value = `充值: ${diff.toFixed(2)}`;
                } else {
                    value = `无变化: ${diff.toFixed(2)}`;
                }
                
                costData.push({
                    time: rows[i].read_time,
                    value: value
                });
            }
            return costData;
            
        case 'total':
            // 总量模式: 直接用读表数据
            return rows.map(row => ({
                time: row.read_time,
                value: `读数: ${row.total_reading}`
            }));
            
        case 'balance':
            // 余额模式: 直接显示remainingBalance
            return rows.map(row => ({
                time: row.read_time,
                value: `余额: ${parseFloat(row.remainingBalance).toFixed(2)}`
            }));
            
        default:
            return rows.map(row => ({
                time: row.read_time,
                value: 'N/A'
            }));
    }
}

// 创建迷你图表
function createMiniChart(deviceData, card) {
    const ctx = card.querySelector('.mini-chart').getContext('2d');
    
    // 销毁之前的图表实例（如果存在）
    const chartId = deviceData.device_id;
    if (window.miniCharts && window.miniCharts[chartId]) {
        window.miniCharts[chartId].destroy();
    }
    
    // 准备图表数据
    const chartData = prepareMiniChartData(deviceData.rows);
    
    // 创建新图表
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: getChartLabel(),
                data: chartData.values,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                pointRadius: 2,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    },
                    title: {
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    },
                    title: {
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    titleColor: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666',
                    bodyColor: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666',
                    backgroundColor: document.body.classList.contains('dark-mode') ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.8)'
                }
            }
        }
    });
    
    // 保存图表引用
    if (!window.miniCharts) {
        window.miniCharts = {};
    }
    window.miniCharts[chartId] = chart;
}

// 准备迷你图表数据
function prepareMiniChartData(rows) {
    if (!rows || rows.length === 0) {
        return { labels: [], values: [] };
    }
    
    // 反转数组以正确显示时间序列
    const reversedRows = [...rows].reverse();
    
    switch (currentMode) {
        case 'usage':
            // 用量模式: 新total_reading - 旧total_reading
            const usageLabels = [];
            const usageValues = [];
            
            for (let i = 0; i < reversedRows.length - 1; i++) {
                const currentReading = parseFloat(reversedRows[i + 1].total_reading);
                const previousReading = parseFloat(reversedRows[i].total_reading);
                const usage = currentReading - previousReading;
                
                usageLabels.push(reversedRows[i + 1].read_time);
                usageValues.push(usage);
            }
            
            return { labels: usageLabels, values: usageValues };
            
        case 'cost':
            // 用钱模式: 新remainingBalance - 旧remainingBalance
            const costLabels = [];
            const costValues = [];
            
            for (let i = 0; i < reversedRows.length - 1; i++) {
                const currentBalance = parseFloat(reversedRows[i + 1].remainingBalance);
                const previousBalance = parseFloat(reversedRows[i].remainingBalance);
                const cost = previousBalance - currentBalance; // 消耗为正数
                
                costLabels.push(reversedRows[i + 1].read_time);
                costValues.push(cost);
            }
            
            return { labels: costLabels, values: costValues };
            
        case 'total':
            // 总量模式: 直接用读表数据
            return {
                labels: reversedRows.map(row => row.read_time),
                values: reversedRows.map(row => parseFloat(row.total_reading))
            };
            
        case 'balance':
            // 余额模式: 直接显示remainingBalance
            return {
                labels: reversedRows.map(row => row.read_time),
                values: reversedRows.map(row => parseFloat(row.remainingBalance))
            };
            
        default:
            return { labels: [], values: [] };
    }
}

// 显示图表
function showChart(deviceData) {
    const modal = document.getElementById('chart-modal');
    const modalTitle = document.getElementById('modal-title');
    const canvas = document.getElementById('chart-canvas');
    
    // 设置模态框标题
    modalTitle.textContent = `${deviceData.equipmentName} 数据图表`;
    
    // 显示模态框
    modal.style.display = 'block';
    
    // 准备图表数据
    const chartData = prepareChartData(deviceData.rows);
    
    // 销毁之前的图表实例（如果存在）
    if (window.currentChart) {
        window.currentChart.destroy();
    }
    
    // 创建新图表
    const ctx = canvas.getContext('2d');
    window.currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [{
                label: getChartLabel(),
                data: chartData.values,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    },
                    title: {
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    }
                },
                x: {
                    ticks: {
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    },
                    title: {
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666'
                    }
                },
                tooltip: {
                    titleColor: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666',
                    bodyColor: document.body.classList.contains('dark-mode') ? '#ffffff' : '#666666',
                    backgroundColor: document.body.classList.contains('dark-mode') ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.8)'
                }
            }
        }
    });
}

// 显示详细信息
function showDetailedInfo(deviceData) {
    const modal = document.getElementById('detail-modal');
    const modalTitle = document.getElementById('detail-modal-title');
    const detailContent = document.getElementById('detail-content');
    
    // 设置模态框标题
    modalTitle.textContent = `${deviceData.equipmentName} 详细信息`;
    
    // 构建详细信息内容
    const isElectric = deviceData.equipmentType === '0' || deviceData.equipmentType === 0;
    const deviceType = isElectric ? '电表' : '水表';
    
    const displayData = calculateDisplayData(deviceData.rows);
    
    detailContent.innerHTML = `
        <div class="detail-info">
            <div class="detail-info-item">
                <span class="detail-info-label">设备ID:</span>
                <span>${deviceData.device_id}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">设备类型:</span>
                <span>${deviceType}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">安装位置:</span>
                <span>${deviceData.installationSite}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">状态:</span>
                <span>${deviceData.status === '1' || deviceData.status === 1 ? '启用' : '停用'}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">倍率:</span>
                <span>${deviceData.ratio}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">单价:</span>
                <span>${deviceData.rate}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">财务账户号:</span>
                <span>${deviceData.acctId}</span>
            </div>
            <div class="detail-info-item">
                <span class="detail-info-label">最后更新:</span>
                <span>${deviceData.updated_at}</span>
            </div>
        </div>
        <div class="detail-data">
            <h3>数据记录</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>${currentMode === 'usage' ? '用量' : currentMode === 'cost' ? '金额变化' : '总读数'}</th>
                    </tr>
                </thead>
                <tbody>
                    ${displayData.map(item => `
                        <tr>
                            <td>${item.time}</td>
                            <td>${item.value}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    // 显示模态框
    modal.style.display = 'block';
}

// 准备图表数据
function prepareChartData(rows) {
    if (!rows || rows.length === 0) {
        return { labels: [], values: [] };
    }
    
    // 反转数组以正确显示时间序列
    const reversedRows = [...rows].reverse();
    
    switch (currentMode) {
        case 'usage':
            // 用量模式: 新total_reading - 旧total_reading
            const usageLabels = [];
            const usageValues = [];
            
            for (let i = 0; i < reversedRows.length - 1; i++) {
                const currentReading = parseFloat(reversedRows[i + 1].total_reading);
                const previousReading = parseFloat(reversedRows[i].total_reading);
                const usage = currentReading - previousReading;
                
                usageLabels.push(reversedRows[i + 1].read_time);
                usageValues.push(usage);
            }
            
            return { labels: usageLabels, values: usageValues };
            
        case 'cost':
            // 用钱模式: 新remainingBalance - 旧remainingBalance
            const costLabels = [];
            const costValues = [];
            
            for (let i = 0; i < reversedRows.length - 1; i++) {
                const currentBalance = parseFloat(reversedRows[i + 1].remainingBalance);
                const previousBalance = parseFloat(reversedRows[i].remainingBalance);
                const cost = previousBalance - currentBalance; // 消耗为正数
                
                costLabels.push(reversedRows[i + 1].read_time);
                costValues.push(cost);
            }
            
            return { labels: costLabels, values: costValues };
            
        case 'total':
            // 总量模式: 直接用读表数据
            return {
                labels: reversedRows.map(row => row.read_time),
                values: reversedRows.map(row => parseFloat(row.total_reading))
            };
            
        case 'balance':
            // 余额模式: 直接显示remainingBalance
            return {
                labels: reversedRows.map(row => row.read_time),
                values: reversedRows.map(row => parseFloat(row.remainingBalance))
            };
            
        default:
            return { labels: [], values: [] };
    }
}

// 获取图表标签
function getChartLabel() {
    switch (currentMode) {
        case 'usage': return '用量';
        case 'cost': return '消耗金额';
        case 'total': return '总读数';
        case 'balance': return '余额';
        default: return '数据';
    }
}

// 搜索设备
async function searchDevices(keyword) {
    // 检查关键词长度
    if (keyword.length < 2) {
        alert("请输入两个以上的字符。");
        return;
    }
    
    // 限制关键词长度为8个字符
    if (keyword.length > 8) {
        alert("搜索关键词不能超过8个字符。");
        return;
    }
    
    try {
        // 使用默认API地址，如果配置已加载则使用配置的地址
        const apiUrl = CONFIG && CONFIG.API_BASE_URL ? CONFIG.API_BASE_URL : 'http://localhost:8080';
        const response = await fetchWithTimeout(`${apiUrl}/?mode=search&key_word=${encodeURIComponent(keyword)}`);
        const data = await response.json();
        
        if (data.code === 418) {
            // 搜索关键词太短
            alert(data.error_talk);
        } else if (data.code === 200 && data.search_status === 0) {
            // 搜索成功，创建设备ID列表
            const deviceIds = data.rows.map(row => row.device_id);
            
            // 保存设备ID列表
            currentDeviceIds = deviceIds;
            
            // 检查是否有搜索结果
            if (data.total === 0 || deviceIds.length === 0) {
                // 没有找到结果
                const cardsContainer = document.getElementById('cards-container');
                cardsContainer.innerHTML = '<p>什么也没找到哦 ╮(╯▽╰)╭</p>';
            } else {
                // 加载每个设备的详细数据
                await loadDeviceDataForIds(currentDeviceIds, data.total);
            }
        } else {
            console.error('搜索设备失败:', data);
            alert("搜索设备失败，请稍后重试。");
        }
    } catch (error) {
        console.error('搜索设备时出错:', error);
        alert("搜索设备时出错，请检查网络连接。");
    }
}