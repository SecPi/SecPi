


var app = angular.module("SecPi", []);

app.controller('DataController', function($http, $log, $scope, $timeout){
		var self = this;
		
		self.flash_message = null;
		self.flash_type = 'info';
		
		self.data = [];
		self.fields = {};
		
		self.edit_data = null;
		self.edit_id = 0;
		self.orig_data = null;
		
		self.flash = function(message,type){
			self.flash_message = message;
			self.flash_type = type;
			
			$timeout(function(){self.flash_message = null}, 5000)
		}
		
		
		self.fetchFields = function(){
			$http.post(BASE_LINK+'/fieldList', {}).then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						self.fields = response.data['data'];
					}
					else{
						self.flash(response.data['message'], 'error');
					}
				},
				function (response) {
					// error
					self.flash('Error retrieving data!', 'error');
				}
			)
		}
		
		self.getFields = function(filter){
			return self.filter_fields(filter);
		}
		
		self.filter_fields = function(filter) {
			var filtered_fields = {};
			
			for (var key in self.fields) {
				if (self.fields.hasOwnProperty(key)) {
					if($.inArray(filter, self.fields[key]['visible']) >= 0){
						filtered_fields[key] = self.fields[key];
					}
				}
			}
			
			return filtered_fields;
		}
		
		
		self.getList = function(){
			$log.log('fetching list')
			$http.get(BASE_LINK+'/list').then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						self.data = response.data['data'];
					}
					else{
						self.flash(response.data['message'], 'error');
					}
				},
				function (response) {
					// error
					self.flash('Error retrieving data!', 'error');
				})	
		};
		
		self.showEdit = function(id){
			self.edit_data = self.data[id];
			self.edit_id = id;
			self.orig_data = jQuery.extend(true, {}, self.data[id])
			self.dialog.dialog("open");
		};
		
		self.saveEdit = function(){ 
			$log.log("adding stuff")
			
			$http.post(BASE_LINK+'/update', self.edit_data).then(
				function (response) {
					// success
					if(response.data['status'] == 'success'){
						self.flash(response.data['message'], 'info')
						self.dialog.dialog( "close" );
					}
					else{
						sself.flash(response.data['message'], 'error');
					}
				},
				function (response) {
					// error
					self.flash('Error saving data!', 'error');
				}
			)
		};
		
		self.cancelEdit = function(){
			$log.log("cancel");
			self.data[self.edit_id] = self.orig_data;
			self.orig_data = null;
			self.edit_data = null;
			$scope.$apply();
			self.dialog.dialog( "close" );
		};
		
		$timeout(function(){
			self.dialog = $( "#edit-form-div" ).dialog({
				autoOpen: false,
				height: 300,
				width: 350,
				modal: true,
				buttons: {
					"Save": function(){
						self.saveEdit();
					},
					Cancel: function() {
						self.cancelEdit();
					}
				}
			});
			
			$( "#edit-form-div" ).on('dialogclose', function(event) {
				self.cancelEdit();
			});
			
		}, 100)
		
		self.fetchFields();
})



