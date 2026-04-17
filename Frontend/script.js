let chart; 

// ---------------- YEAR SLIDER ---------------- 
function updateYear(){ 
    document.getElementById("yearDisplay").innerText = 
        document.getElementById("yearSlider").value; 
    // 🔥 Live heatmap update
    refreshHeatmap();
} 

// ---------------- HELPERS ---------------- 
function normalizeName(rawCounty){
    if(!rawCounty) return "";
    let upper = rawCounty.trim().toUpperCase();
    const mapping = {
        "NAIROBI": "Nairobi", "MOMBASA": "Mombasa", "KISUMU": "Kisumu", "NAKURU": "Nakuru",
        "KIAMBU": "Kiambu", "MACHAKOS": "Machakos", "KAJIADO": "Kajiado", "UASIN GISHU": "Uasin Gishu",
        "KAKAMEGA": "Kakamega", "BUNGOMA": "Bungoma", "BUSIA": "Busia", "SIAYA": "Siaya",
        "HOMA BAY": "Homa Bay", "MIGORI": "Migori", "KISII": "Kisii", "NYAMIRA": "Nyamira",
        "KERICHO": "Kericho", "BOMET": "Bomet", "NAROK": "Narok", "TURKANA": "Turkana",
        "WEST POKOT": "West Pokot", "SAMBURU": "Samburu", "TRANS NZOIA": "Trans Nzoia",
        "ELGEYO-MARAKWET": "Elgeyo Marakwet", "ELGEYO MARAKWET": "Elgeyo Marakwet",
        "ELEGEYO-MARAKWET": "Elgeyo Marakwet", "BARINGO": "Baringo",
        "NANDI": "Nandi", "LAIKIPIA": "Laikipia", "NYANDARUA": "Nyandarua", "MURANG'A": "Murang'a",
        "MURANGA": "Murang'a", "KIRINYAGA": "Kirinyaga", "NYERI": "Nyeri", "EMBU": "Embu",
        "THARAKA - NITHI": "Tharaka Nithi", "THARAKA NITHI": "Tharaka Nithi", "MERU": "Meru",
        "ISIOLO": "Isiolo", "MARSABIT": "Marsabit", "GARISSA": "Garissa", "WAJIR": "Wajir",
        "MANDERA": "Mandera", "TANA RIVER": "Tana River", "LAMU": "Lamu", "TAITA TAVETA": "Taita Taveta",
        "KWALE": "Kwale", "KILIFI": "Kilifi", "KITUI": "Kitui", "MAKUENI": "Makueni", "VIHIGA": "Vihiga"
    };
    return mapping[upper] || (rawCounty.charAt(0).toUpperCase() + rawCounty.slice(1).toLowerCase());
}

// Color function 
function getColor(risk){ 
    if(risk === "High") return "#ef4444"; 
    if(risk === "Medium") return "#f59e0b"; 
    return "#10b981"; 
} 

// ---------------- MAP ---------------- 
let map = L.map('map').setView([-1.286389, 36.817223], 6); 

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { 
    attribution: '© OpenStreetMap contributors' 
}).addTo(map); 

let kenyaLayer; 
let geoJsonData;

// ---------------- INITIAL MAP LOAD ---------------- 
async function initMap(){ 
    const res = await fetch("kenya.json"); 
    geoJsonData = await res.json(); 

    kenyaLayer = L.geoJSON(geoJsonData, { 
        style: function(feature){ 
            return { 
                fillColor: "#444", 
                fillOpacity: 0.4, 
                color: "white", 
                weight: 1 
            }; 
        }, 
        onEachFeature: function(feature, layer){ 
            let rawCounty = feature.properties.COUNTY_NAM; 
            let county = normalizeName(rawCounty);

            layer.on("mouseover", function(){ 
                layer.bindPopup(`<b>${county}</b>`).openPopup(); 
            }); 

            layer.on("click", function(){ 
                document.getElementById("region").value = county; 
                predict(); 
            }); 
        } 
    }).addTo(map); 

    // Once map is ready, run first heatmap analysis
    refreshHeatmap();
    predict();
}

// ---------------- AI HEATMAP UPDATE (PERSISTENT COLORS) ---------------- 
async function refreshHeatmap(){ 
    if(!kenyaLayer) return;

    const disease = document.getElementById("disease").value; 
    const year = document.getElementById("yearSlider").value; 

    console.log("AI Heatmap analyzing all counties...");

    kenyaLayer.eachLayer(function(layer){
        let rawCounty = layer.feature.properties.COUNTY_NAM; 
        let county = normalizeName(rawCounty);

        // Alias for AI model missing data
        const regionForAI = (county === "Baringo") ? "Nakuru" : county;

        fetch("http://localhost:5000/predict", { 
            method: "POST", 
            headers: {"Content-Type": "application/json"}, 
            body: JSON.stringify({ 
                region: regionForAI, 
                disease: disease, 
                year: year 
            }) 
        }) 
        .then(res => res.json()) 
        .then(result => { 
            if(result.error) return; 
            let color = getColor(result.risk); 
            
            // 🔥 Update layer style WITHOUT removing/recreating it
            layer.setStyle({ 
                fillColor: color, 
                fillOpacity: 0.7 
            }); 
            layer.bindPopup(`<b>${county}</b><br>Risk: ${result.risk}<br>Cases: ${result.cases}`);
        }); 
    });
} 

// ---------------- PREDICT ---------------- 
function predict(){ 

    let selectedRegion = document.getElementById("region").value;
    
    // 🔥 Handle Baringo (Alias to Nakuru for prediction if missing from model)
    const regionForAI = (selectedRegion === "Baringo") ? "Nakuru" : selectedRegion;

    const data = { 
        region: regionForAI, 
        disease: document.getElementById("disease").value, 
        year: document.getElementById("yearSlider").value 
    }; 

    fetch("http://localhost:5000/predict", { 
        method: "POST", 
        headers: {"Content-Type": "application/json"}, 
        body: JSON.stringify(data) 
    }) 
    .then(res => res.json()) 
    .then(res => { 

        if(res.error){ 
            alert(res.error); 
            return; 
        } 

        document.getElementById("risk").innerText = res.risk; 
        document.getElementById("cases").innerText = res.cases; 
        document.getElementById("trend").innerText = res.trend; 
        document.getElementById("beds").innerText = res.beds; 

        document.getElementById("alert").innerText = res.alert; 
        document.getElementById("recommendation").innerText = res.recommendation; 

        // Card color 
        let card = document.getElementById("riskCard"); 
        card.classList.remove("high","medium","low"); 

        if(res.risk === "High") card.classList.add("high"); 
        if(res.risk === "Medium") card.classList.add("medium"); 
        if(res.risk === "Low") card.classList.add("low"); 

        drawChart(res.cases); 
        
        // 🔥 Refresh heatmap
        refreshHeatmap(); 
    })
    .catch(err => {
        console.error("Connection Error:", err);
    });
} 

// ---------------- CHART ---------------- 
function drawChart(cases){ 

    const ctx = document.getElementById("trendChart"); 

    const data = [ 
        cases * 0.6, 
        cases * 0.8, 
        cases 
    ]; 

    if(chart) chart.destroy(); 

    chart = new Chart(ctx, { 
        type: 'line', 
        data: { 
            labels: ["2023", "2024", "2025"], 
            datasets: [{ 
                label: "Cases Trend", 
                data: data, 
                borderWidth: 3,
                borderColor: "#3b82f6",
                tension: 0.4
            }] 
        },
        options: {
            plugins: { legend: { labels: { color: "white" } } },
            scales: {
                x: { ticks: { color: "white" } },
                y: { ticks: { color: "white" } }
            }
        }
    }); 
} 

// ---------------- PDF ---------------- 
function downloadPDF(){ 
    const { jsPDF } = window.jspdf; 
    const doc = new jsPDF(); 

    const username = localStorage.getItem('username') || "User";
    const date = new Date().toLocaleDateString();

    // Header
    doc.setFontSize(22);
    doc.setTextColor(59, 130, 246);
    doc.text("AI Health Intelligence Report", 20, 30);
    
    doc.setFontSize(12);
    doc.setTextColor(100, 116, 139);
    doc.text(`Generated by: ${username}`, 20, 40);
    doc.text(`Date: ${date}`, 20, 47);
    
    // Selection Details
    doc.setDrawColor(200, 200, 200);
    doc.line(20, 55, 190, 55);
    
    doc.setTextColor(0, 0, 0);
    doc.setFontSize(14);
    doc.text("Analysis Parameters", 20, 65);
    doc.setFontSize(12);
    doc.text("Region: " + document.getElementById("region").value, 20, 75); 
    doc.text("Disease: " + document.getElementById("disease").value, 20, 82); 
    doc.text("Year: " + document.getElementById("yearSlider").value, 20, 89); 
 
    // Prediction Results
    doc.setFontSize(14);
    doc.text("Prediction Results", 20, 105);
    doc.setFontSize(12);
    doc.text("Risk Level: " + document.getElementById("risk").innerText, 20, 115); 
    doc.text("Predicted Cases: " + document.getElementById("cases").innerText, 20, 122); 
    doc.text("Trend: " + document.getElementById("trend").innerText, 20, 129); 
    doc.text("Beds Needed: " + document.getElementById("beds").innerText, 20, 136); 
 
    // Recommendation
    doc.setFontSize(14);
    doc.text("Public Health Recommendation", 20, 150);
    doc.setFontSize(11);
    const recText = document.getElementById("recommendation").innerText;
    const splitText = doc.splitTextToSize(recText, 170);
    doc.text(splitText, 20, 160); 

    doc.setFontSize(10);
    doc.setTextColor(150, 150, 150);
    doc.text("© 2026 HealthIntel AI System - Confidential Data", 20, 280);
 
    doc.save(`Health_Report_${document.getElementById("region").value}.pdf`); 
} 

// Add listeners
document.getElementById("disease").addEventListener("change", refreshHeatmap);

// Initial Load
initMap();
