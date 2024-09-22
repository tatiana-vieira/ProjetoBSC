<canvas id="metasChart"></canvas>
<canvas id="acoesChart"></canvas>

<script>
  // Gráfico de Metas Atingidas
  var ctxMetas = document.getElementById('metasChart').getContext('2d');
  var metasChart = new Chart(ctxMetas, {
    type: 'bar',
    data: {
        labels: ['Metas'],
        datasets: [{
            label: '% Metas Atingidas',
            data: [{{ percentual_metas_atingidas }}],
            backgroundColor: '#36a2eb'
        }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    }
  });

  // Gráfico de Ações Concluídas
  var ctxAcoes = document.getElementById('acoesChart').getContext('2d');
  var acoesChart = new Chart(ctxAcoes, {
    type: 'bar',
    data: {
        labels: ['Ações'],
        datasets: [{
            label: '% Ações Concluídas',
            data: [{{ percentual_acoes_concluidas }}],
            backgroundColor: '#ff6384'
        }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    }
  });
</script>
