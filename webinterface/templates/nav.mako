<%page args="active_tab" />

<ul class="tabrow">
	<li id="home"><a href="/">Home</a></li>
	<li id="activate"><a href="/activate">Activate</a></li>
	<li id="sensors"><a href="/sensors">Sensors</a></li>
	<li id="zones"><a href="/zones">Zones</a></li>
	<li id="setups"><a href="/setups">Setups</a></li>
	<li id="alarms"><a href="/alarms">Alarms</a></li>
	<li id="workers"><a href="/workers">Workers</a></li>
	<li id="actions"><a href="/actions">Actions</a></li>
	<li id="actionparams"><a href="/actionparams">Action Params</a></li>
	<li id="logs"><a href="/logs">Logs</a></li>
</ul>



<script type="text/javascript">
	$("#${active_tab}").addClass('selected')
</script>