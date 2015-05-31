<%inherit file="main.mako"/>
<%block name="subnav">
<%include file="subnav.mako" />
</%block>
<%!
	from tools import utils
%>
% if data is not None and len(data) > 0 and fields is not None and len(fields)>0:
	<table class="list">
		<tr class="listheader">
<%
filtered_fields = utils.filter_fields(fields, 'list')
%>
		% for field,finfo in filtered_fields.iteritems():
			<th>${finfo['name']}</th>
		%endfor
			<th>&nbsp;</th><!-- for delete button -->
		</tr>
		% for obj in data:
			<tr>
			% for field, finfo in filtered_fields.iteritems():
				<td>${obj.__dict__[field]}</td>
			% endfor
				<td><a href="delete?id=${obj.id}">delete</a></td>
			</tr>
		% endfor
	</table>
% else:
	No data found!
% endif