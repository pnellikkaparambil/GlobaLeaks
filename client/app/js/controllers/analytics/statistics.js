GL.controller("StatisticsCtrl", ["$scope", "$http", function ($scope, $http) {
    $scope.charts = [];
    $scope.error = false;
    $scope.options = { legend: { display: false } };
    $http.get("api/analyst/stats")
        .then(function(data) {$scope.dataPie(true,data) })
        .catch(function(err) { $scope.dataPie(false, err) })
    $scope.dataPie = function(success,data) {
        if(success){
            var result = data.data;
            var pieOne = {
                title : "Accessi con o senza ricevuta",
                labels :[result.no_access.label, result.at_least_one_access.label],
                values :[result.no_access.value, result.at_least_one_access.value]
            };
            var pieTwo = {
                title: "Segnalazioni anonime/sottoscritte",
                labels :[result.anonymous_tips.label, result.subscribed_tips.label, result.subscribed_later_tips.label],
                values :[result.anonymous_tips.value, result.subscribed_tips.value, result.subscribed_later_tips.value]
            }
            $scope.charts.push(pieOne,pieTwo);
        } else {
            console.error(data)
            $scope.error = true;
        }
    }
}]);
