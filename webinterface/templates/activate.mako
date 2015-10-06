<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "activate" %></%def>

<h1> Activate SecPi</h1>


% if (active_setups is not None and len(active_setups) > 0) or (inactive_setups is not None and len(inactive_setups) > 0):
	% if (active_setups is not None and len(active_setups) > 0):
		<form method="post" action="/activate">
			<select name="deactivate_setup", id="deactivate_setup">
			% for setup in active_setups:
				<option value="${setup.id}">${setup.name}</option>
			%endfor
			</select>
			<input type="submit" value="deactivate" />
		</form>
	%endif
	<br />
	%if (inactive_setups is not None and len(inactive_setups) > 0):
		<form method="post" action="/activate">
			<select name="activate_setup", id="activate_setup">
			% for setup in inactive_setups:
				<option value="${setup.id}">${setup.name}</option>
			%endfor
			</select>
			<input type="submit" value="activate" />
		</form>
	%endif
%else:
	No setups found, please configure your SecPi first!
%endif


<div ng-controller="LogController as logCtrl">
	<div class="log_entry" ng-repeat="log in logCtrl.log_entries" ng-show="log.message != null" ng-class="'lvl'+log.level">
		{{log.logtime}} {{log.message}}
		<span class="log_ack"><img src="/static/img/icons/tick.png" title="acknowledge" ng-click="logCtrl.ack($index)" /></span>
	</div>
</div>