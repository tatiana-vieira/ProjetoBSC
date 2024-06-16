/* static/js/scripts.js */

document.addEventListener("DOMContentLoaded", function() {
    console.log("Scripts carregados!");
    const ctx1 = document.getElementById('chart-historico-metas').getContext('2d');
    const ctx2 = document.getElementById('chart-historico-acoes').getContext('2d');

    new Chart(ctx1, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [{
                label: 'Metas',
                data: [12, 19, 3, 5, 2, 3, 8, 12, 7, 5, 6, 10],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            datasets: [{
                label: 'Ações',
                data: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
                borderColor: 'rgba(153, 102, 255, 1)',
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
});