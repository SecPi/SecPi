
var app = angular.module("SecPi", []);

app.controller('TestController', function($http, $log){
		var self = this;
		
		self.flash_message = null;
		self.flash_type = 'info';
		
		self.data = [];
		self.fields = {};
		
		self.edit_data = null;
		
		
		
		self.fetchFields = function(filter){
			$http.post('/workers/fieldList', {filter: filter}).then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						self.fields = response.data['data'];
					}
					else{
						self.flash_message = response.data['message'];
						self.flash_type='error';
					}
				},
				function (response) {
					// error
					self.flash_message = 'Error retrieving data!';
					self.flash_type='error';
				}
			)
		}
		
		self.getList = function(){
			$log.log('fetching list')
			self.fetchFields('list')
			$http.get('/workers/list').then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						self.data = response.data['data'];
					}
					else{
						self.flash_message = response.data['message'];
						self.flash_type='error';
					}
				},
				function (response) {
					// error
					self.flash_message = 'Error retrieving data!';
					self.flash_type='error';
				})	
		};
		
		self.showEdit = function(id){
			$log.log("editing id: " +id)
			self.fetchFields('update')
			self.edit_data = self.data[id]
		};
		
		self.saveEdit = function(){
				
		};
})