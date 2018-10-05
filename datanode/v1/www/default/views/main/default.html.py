
<section class="inner">

	<header>
		<h1>Welcome to INDIGO</h1>
		<h2>Indigo is a Ledgable product released under the GPLv3 license</h2>
	</header>
	
	<p>For information regarding the license please see <a href="https://www.gnu.org/licenses/gpl-3.0.en.html" target="__blank" class="link">https://www.gnu.org/licenses/gpl-3.0.en.html</a></p>

	<h2>Success !!</h2>

	<p>You are successfully connected to an Indigo Data-Node. This is the default page</p>

	<section class="var_info">

		<h3>Chains on this datanode</h3>
	
		<ul class="chains">

<py>

# This calls the NodeController code to retreive the chain-ids

chains_ = self.chains()

if (chains_ != None):
	for chain_ in chains_:
		print("""<li class="chain">%s</li>""" % (chain_), file=stdout)

</py>
	
		</ul>
			
	</section>
	
	<h3 data-event="{'action':'Example.Extended','event':'testjscall','args':{'uid':'12345'}}">Click here to test AJAX Post</h3>

	<p>AJAX (or Asynchronous Javascript Execution) is a method to push data to the server without causing a page refresh</p>
	
	<p>This allows for customized content to be rendered as required or form data to be passed resulting in UI or interaction changes</p>
	
	<p>The datanode comes with a basic model to enable you to push data to a datanode endpoint (see the file 'TestController.py') and the Javascript code 'app.example.js'</p>
	
	<h3>Further Info</h3>
	
	<p>To customize this page, css and so forth, see the <strong>www/default</strong> folder in the root of the service installation</p>

	<pyinclude>views/__bits/appvars.html.py</pyinclude>

	<pyinclude>views/__bits/page/footer.html.py</pyinclude>

</section>
