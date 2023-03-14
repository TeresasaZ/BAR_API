from flask_restx import Namespace, Resource
from markupsafe import escape
from api.utils.bar_utils import BARUtils
from flask import request
import re
import subprocess
import requests
from api.utils.pymol_script import PymolCmds
import sys
from api import db, cache, limiter
from sqlalchemy import text


snps = Namespace("SNPs", description="Information about SNPs", path="/snps")

parser = snps.parser()
parser.add_argument(
    "snps",
    type=str,
    action="append",
    required=True,
    help="SNP locations, format: OriLocMut i.e. V25L",
    default=["V25L", "E26A"],
)
parser.add_argument(
    "chain",
    type=str,
    help="[Optional]\n For multimers, enter chain ID only (i.e. A)\n For monomers, remain 'None' as default.",
    default="None",
)


@snps.route("/phenix/<fixed_pdb>/<moving_pdb>")
class Phenix(Resource):
    @snps.param("fixed_pdb", _in="path", default="Potri.016G107900.1")
    @snps.param("moving_pdb", _in="path", default="AT5G01040.1")
    def get(self, fixed_pdb="", moving_pdb=""):
        """
        This end point returns the superimposition of the moving PDB onto the fixed PDB (returns a URL to fetch PDB)
        Enter valid species identifier for proteins of interest
        """

        fixed_pdb = escape(fixed_pdb)
        moving_pdb = escape(moving_pdb)

        arabidopsis_pdb_path = "/var/www/html/eplant_legacy/java/Phyre2-Models/Phyre2_"
        poplar_pdb_path = "/var/www/html/eplant_poplar/pdb/"
        tomato_pdb_path = "/var/www/html/eplant_tomato/pdb/"
        phenix_pdb_link = "//bar.utoronto.ca/phenix-pdbs/"
        phenix_pdb_path = "/var/www/html/phenix-pdbs/"

        # Check if genes ids are valid
        if BARUtils.is_arabidopsis_gene_valid(fixed_pdb):
            fixed_pdb_path = arabidopsis_pdb_path + fixed_pdb.upper() + ".pdb"
        elif BARUtils.is_poplar_gene_valid(fixed_pdb):
            fixed_pdb_path = (
                poplar_pdb_path + BARUtils.format_poplar(fixed_pdb) + ".pdb"
            )
        elif BARUtils.is_tomato_gene_valid(fixed_pdb, True):
            fixed_pdb_path = tomato_pdb_path + fixed_pdb.capitalize() + ".pdb"
        else:
            return BARUtils.error_exit("Invalid fixed pdb gene id"), 400

        if BARUtils.is_arabidopsis_gene_valid(moving_pdb):
            moving_pdb_path = arabidopsis_pdb_path + moving_pdb.upper() + ".pdb"
        elif BARUtils.is_poplar_gene_valid(moving_pdb):
            moving_pdb_path = (
                poplar_pdb_path + BARUtils.format_poplar(moving_pdb) + ".pdb"
            )
        elif BARUtils.is_tomato_gene_valid(moving_pdb, True):
            moving_pdb_path = tomato_pdb_path + moving_pdb.capitalize() + ".pdb"
        else:
            return BARUtils.error_exit("Invalid moving pdb gene id"), 400

        # Check if model already exists
        phenix_file_name = fixed_pdb.upper() + "-" + moving_pdb.upper() + "-phenix.pdb"
        response = requests.get("https:" + phenix_pdb_link + phenix_file_name)

        # If not, generate the model
        if response.status_code != 200:
            subprocess.run(
                [
                    "phenix.superpose_pdbs",
                    "file_name=" + phenix_pdb_path + phenix_file_name,
                    fixed_pdb_path,
                    moving_pdb_path,
                ]
            )

        return BARUtils.success_exit(phenix_pdb_link + phenix_file_name)


@snps.route("/<string:species>/<string:gene_id>")
class GeneNameAlias(Resource):
    @snps.param("species", _in="path", default="poplar")
    @snps.param("gene_id", _in="path", default="Potri.019G123900.1")
    @cache.cached()
    def get(self, species="", gene_id=""):
        """Endpoint returns annotated SNP poplar data in order of (to match A th API format):
        AA pos (zero-indexed), sample id, 'missense_variant','MODERATE', 'MISSENSE', codon/DNA base change,
        AA change (DH), pro length, gene ID, 'protein_coding', 'CODING', transcript id, biotype
        values with single quotes are fixed"""
        results_json = []

        # Escape input
        gene_id = escape(gene_id)

        if species == "poplar" and BARUtils.is_poplar_gene_valid(gene_id):
            query_db = db.engines["poplar_nssnp"]
        elif species == "tomato" and BARUtils.is_tomato_gene_valid(gene_id, True):
            query_db = db.engines["tomato_nssnp"]
        elif species == "soybean" and BARUtils.is_soybean_gene_valid(gene_id):
            query_db = db.engines["soybean_nssnp"]
        else:
            return BARUtils.error_exit("Invalid gene id"), 400

        with query_db.connect() as conn:
            rows = conn.execute(
                text(
                    "select * from protein_reference join snps_to_protein join snps_reference where protein_reference.gene_identifier = :gene"
                ),
                {"gene": gene_id},
            )

            # BAR A Th API format is chr, AA pos (zero-indexed), sample id, 'missense_variant',
            # 'MODERATE', 'MISSENSE', codon/DNA base change, AA change (DH),
            # pro length, gene ID, 'protein_coding', 'CODING', transcript id, biotype
            for row in rows:
                itm_lst = [
                    row.chromosome,
                    # snpstbl.chromosomal_loci,
                    int(row.aa_pos) - 1,  # zero index-ed
                    row.sample_id,
                    "missense_variant",
                    "MODERATE",
                    "MISSENSE",
                    str(row.transcript_pos) + row.ref_DNA + ">" + row.alt_DNA,
                    row.ref_aa + row.alt_aa,
                    None,
                    re.sub(r".\d$", "", row.gene_identifier),
                    "protein_coding",
                    "CODING",
                    row.gene_identifier,
                    None,
                ]
                results_json.append(itm_lst)

        # Return results if there are data
        if len(results_json) > 0:
            return BARUtils.success_exit(results_json)
        else:
            return BARUtils.error_exit("There are no data found for the given gene")


@snps.route("/<string:species>/samples")
class SampleDefinitions(Resource):
    @snps.param("species", _in="path", default="tomato")
    @cache.cached()
    def get(self, species=""):
        """
        Endpoint returns sample/individual data for a given dataset(species).
        Data may vary between species.
        """

        aliases = {}

        if species == "tomato":
            with db.engines["tomato_nssnp"].connect() as conn:
                rows = conn.execute(
                    text("select lines_id, species, alias from lines_lookup")
                )

                for row in rows:
                    aliases[row.lines_id] = {"alias": row.alias, "species": row.species}

        elif species == "soybean":
            with db.engines["soybean_nssnp"].connect() as conn:
                rows = conn.execute(
                    text("select sample_id, dataset, dataset_sample from sample_lookup")
                )

                for row in rows:
                    aliases[row.sample_id] = {
                        "dataset": row.dataset,
                        "PI number": row.dataset_sample,
                    }
        else:
            return BARUtils.error_exit("Invalid gene id"), 400

        return BARUtils.success_exit(aliases)


@snps.route("/pymol/<string:model>")
class Pymol(Resource):
    decorators = [limiter.limit("6/minute")]

    @snps.param(
        "model", _in="path", default="Potri.016G107900.1", description="gene ID for PDB"
    )
    @snps.expect(parser)
    def get(self, model):
        """
        This end point returns the SNP mutated PDB of the canonical structure.
        Supported Species = 'Arabidopsis' (AGIs), Poplar (Potri), Tomato (Solyc)
        Enter the gene ID, chain ID (if the structure is multimer) and substitution locations.
        Click 'Add string item' button and enter the SNP (format: [AA ref letter][Loci Num][AA mutant letter] - e.g. E25A) if the task contains multiple substitution locations.
        """
        chain = request.args.get("chain").upper()
        snps = request.args.getlist("snps")

        arabidopsis_pdb_path = "/var/www/html/eplant_legacy/java/Phyre2-Models/Phyre2_"
        poplar_pdb_path = "/var/www/html/eplant_poplar/pdb/"
        tomato_pdb_path = "/var/www/html/eplant_tomato/pdb/"
        pymol_path = "/var/www/html/pymol-mutated-pdbs/"
        pymol_link = "//bar.utoronto.ca/pymol-mutated-pdbs/"
        protein_letters = "ACDEFGHIKLMNPQRSTVWY"
        arabidopsis_pdb_id_link = "//bar.utoronto.ca/eplant_legacy/java/Phyre2-Models/"  # new for Arabidopsis pdb id (i.e. 2wtb)
        arabidopsis_pdb_id_path = (
            "/var/www/html/eplant_legacy/java/Phyre2-Models/"  # new
        )

        # Check if too many mutations
        if len(snps) > 25:
            return BARUtils.error_exit("Too many mutations, limit is 25"), 400

        # Check if gene input is valid
        if BARUtils.is_arabidopsis_gene_valid(model):
            gene_pdb_path = arabidopsis_pdb_path + model.upper() + ".pdb"
        elif BARUtils.is_poplar_gene_valid(model):
            gene_pdb_path = poplar_pdb_path + BARUtils.format_poplar(model) + ".pdb"
        elif BARUtils.is_tomato_gene_valid(model, True):
            gene_pdb_path = tomato_pdb_path + model.capitalize() + ".pdb"

        # new: check pdb id inputs
        elif len(model) == 4:  # pdb id
            # check if local has the pdb file already
            arabidopsis_response = requests.get(
                "https:" + arabidopsis_pdb_id_link + model.lower() + ".pdb"
            )

            # the file cannot be found in both directory
            if arabidopsis_response.status_code == 200:
                gene_pdb_path = (
                    arabidopsis_pdb_id_path + model.lower() + ".pdb"
                )  # lower case

            # conduct rcsb request to check if the pdb id input is valid
            else:
                url = "//files.rcsb.org/download/" + model.upper() + ".pdb"
                rcsb_response = requests.get("https:" + url, allow_redirects=True)

                # valid, then set the rcsb url as file input url
                if rcsb_response.status_code == 200:
                    gene_pdb_path = url
                else:
                    return BARUtils.error_exit("Invalid PDB id"), 400
        else:
            return BARUtils.error_exit("Invalid gene id"), 400

        # Check if all elements in snps are valid format of string
        snps = [x.upper() for x in snps]
        formatted_snps = []
        for each in snps:
            if re.match("^[a-zA-Z][1-9][0-9]*[a-zA-Z]$", each) is None:
                return BARUtils.error_exit("Invalid SNP string format"), 400
            elif each[-1] not in protein_letters or each[0] not in protein_letters:
                return (
                    BARUtils.error_exit("Invalid SNP string for protein letters"),
                    400,
                )
            else:
                formatted_snps.append(each)

        # Check any conflict duplicates (i.e. V25A, V25L)
        no_duplicated_snps = list(set(formatted_snps))  # set to remove dups
        loci = [re.sub("[^0-9]", "", x) for x in no_duplicated_snps]
        conflict_snps_loc = list(set([x for x in loci if loci.count(x) > 1]))
        list_len = len(conflict_snps_loc)
        if list_len > 0:
            return (
                BARUtils.error_exit(
                    "Conflict SNPs input at loci: %s"
                    % [int(x) for x in conflict_snps_loc]
                ),
                400,
            )

        # Sort snps in location in order and generate pdb filename
        no_duplicated_snps.sort(key=lambda x: int(x[1:-1]))
        snps_string = ""
        for each in no_duplicated_snps:
            snps_string += "-" + each

        # new: filename with chain name for multimers0
        if chain != "NONE":
            filename = model.upper() + "-" + chain + snps_string + ".pdb"
        else:
            filename = model.upper() + snps_string + ".pdb"

        # pymol_path = "/var/www/html" + pymol_path the wd for all later pymol tasks. Should be root (/var/www/html) during PROD

        # new: separate the loading url from rcsb and from bar
        if "rcsb" in gene_pdb_path:
            loading_url = gene_pdb_path
        else:  # bar.utoronto.ca server files
            loading_url = str(gene_pdb_path).replace(
                "/var/www/html/", "//bar.utoronto.ca/"
            )

        # 1. chain validation
        # new: checking pdb file instead of running pymol_script.py
        try:
            file = requests.get("https:" + loading_url, allow_redirects=True)
            content = re.sub("\n", "", file.content.decode("utf-8"))
            first_atom_row = re.search(
                "\nATOM(.*)\n", file.content.decode("utf-8")
            ).group(1)
        except AttributeError:
            return BARUtils.error_exit("Invalid entity id"), 400

        alphabet = re.findall("[A-Z]+", first_atom_row.strip())  # Vincent Fix
        if len(alphabet) == 3:  # monomer
            if chain != "NONE":  # but chain input is not none
                return (
                    BARUtils.error_exit("Invalid chain input, the model is monomer"),
                    400,
                )
        else:
            chain_string_index = re.search(
                r"CHAIN:[\s\S]*?;", content
            ).span()  # Looking for a CHAIN header e.g. "COMPND   3 CHAIN: A, B;"
            sliced_chains = content[
                chain_string_index[0] + 6 : chain_string_index[1] - 1
            ].split(
                ","
            )  # e.g. ['A', 'B', 'C']
            chains = []
            for each in sliced_chains:
                chains.append(each[-1])
            if chain not in chains:
                return (
                    BARUtils.error_exit(
                        "Invalid chain input, chains in the model are %s" % chains
                    ),
                    400,
                )

        # 2. original AAs match the model:
        print(snps_string, "snps string", file=sys.stderr)
        validate_aas = PymolCmds.residue_validation(
            loading_url, chain, snps_string.split("-")[1:]
        )
        if validate_aas["status"] is False:
            return BARUtils.error_exit(validate_aas["msg"]), 400

        # Search if the query already exists
        response = requests.get("https:" + pymol_link + filename)

        if response.status_code != 200:
            # Execute mutate_snps, saving at wd_path: /var/www/html/pymol/
            PymolCmds.compute_mutation(
                loading_url, pymol_path + filename, chain, snps_string.split("-")[1:]
            )

        # currently return url of local folder: wd_path/var/www/html/pymol
        # return BARUtils.success_exit(wd_path + pymol_path + filename)
        # should use pymol_link in API:
        return BARUtils.success_exit(pymol_link + filename)
