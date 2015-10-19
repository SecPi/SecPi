<%inherit file="main.mako"/>

<%def name="active_tab()"><% return "500" %></%def>

<h1>Sorry...</h1>
... there was an error rendering the page!

<div id="traceback">
<pre>
${traceback}
</pre>
</div>