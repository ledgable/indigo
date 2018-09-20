
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

	<p>To customize this page, css and so forth, see the <strong>www/default</strong> folder in the root of the service installation</p>

	<pyinclude>views/__bits/appvars.html.py</pyinclude>

	<pyinclude>views/__bits/page/footer.html.py</pyinclude>

</section>
