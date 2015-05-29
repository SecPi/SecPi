<%inherit file="main.mako"/>

% if fields is not None and len(fields)>0:
	<form method="post" action="add">
	<table>
		% for field,desc in fields.iteritems():
			<tr>
				<td>${desc}</td>
				<td><input type="text" name="${field}" id="${field}" /></td>
			</tr>
		%endfor
			<tr>
				<td>Submit</td>
				<td><input type="submit" value="Submit" /></td>
			</tr>
	</table>
	</form>
% else:
	No data found!
% endif