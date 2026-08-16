import re


GREETING_ONLY = {
    # Common greetings
    "hi",
    "hello",
    "hey",
    "hiya",
    "howdy",
    "yo",
    "sup",
    "wassup",
    "what's up",
    "whats up",

    # Time-based greetings
    "good morning",
    "good afternoon",
    "good evening",
    "good night",

    # Informal greetings
    "hey there",
    "hi there",
    "hello there",
    "hey hey",
    "hi hi",
    "hello hello",
    "yo there",

    # Greeting + politeness
    "hi thanks",
    "hello thanks",
    "hey thanks",

    # Very short conversational openers
    "how are you",
    "how are things",
    "how's it going",
    "hows it going",
    "how are you doing",
    "how have you been",
    "how's everything",
    "hows everything",
    "what's going on",
    "whats going on",
}


WORKFLOW_TERMS = {
    # Galaxy
    "galaxy",
    "galaxy project",
    "galaxy workflow",
    "galaxy tool",
    "galaxy tools",
    "galaxy toolset",
    "galaxy toolshed",
    "galaxy tool shed",
    "galaxy history",
    "galaxy dataset",
    "galaxy datasets",
    "galaxy server",
    "galaxy instance",
    "workflowhub",
    "workflow hub",
    "toolshed",
    "tool shed",

    # Workflow concepts
    "workflow",
    "workflows",
    "workflow step",
    "workflow steps",
    "workflow design",
    "workflow planning",
    "workflow generation",
    "workflow construction",
    "workflow execution",
    "workflow validation",
    "workflow analysis",
    "workflow tool",

    # Genomics / bioinformatics
    "bioinformatics",
    "genomics",
    "genome",
    "genome analysis",
    "genomic analysis",
    "sequence analysis",
    "sequencing",
    "dna",
    "rna",
    "mrna",
    "transcriptomics",
    "epigenomics",
    "proteomics",
    "metagenomics",
    "metatranscriptomics",

    # RNA-seq
    "rna-seq",
    "rnaseq",
    "rna seq",
    "single-cell rna-seq",
    "scrna-seq",
    "scrnaseq",
    "single cell",
    "bulk rna-seq",
    "differential expression",
    "gene expression",
    "transcript quantification",
    "transcriptome",
    "transcriptomics",

    # DNA / variants
    "dna sequencing",
    "whole genome sequencing",
    "wgs",
    "whole exome sequencing",
    "wes",
    "exome",
    "variant calling",
    "variant analysis",
    "genetic variants",
    "variants",
    "snp",
    "snps",
    "single nucleotide polymorphism",
    "indel",
    "indels",
    "vcf",
    "variant annotation",
    "genotype",
    "genotyping",

    # Common sequencing technologies / data
    "ngs",
    "next generation sequencing",
    "illumina",
    "nanopore",
    "pacbio",
    "long read sequencing",
    "short read sequencing",
    "fastq",
    "fasta",
    "bam",
    "sam",
    "cram",
    "bed",
    "gff",
    "gff3",
    "gtf",

    # Common bioinformatics operations
    "quality control",
    "quality assessment",
    "read alignment",
    "sequence alignment",
    "alignment",
    "mapping",
    "assembly",
    "genome assembly",
    "read trimming",
    "adapter trimming",
    "annotation",
    "genome annotation",
    "gene annotation",
    "functional annotation",
    "phylogenetics",
    "phylogenetic analysis",

    # Biological domains
    "genetics",
    "molecular biology",
    "molecular genetics",
    "microbiology",
    "immunology",
    "cancer genomics",
    "population genomics",
    "comparative genomics",
    "systems biology",
}


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s']", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def is_greeting_only(text: str) -> bool:
    return normalize(text) in GREETING_ONLY


def has_workflow_signal(text: str) -> bool:
    text = normalize(text)
    return any(term in text for term in WORKFLOW_TERMS)


def check_rules(text: str) -> str:
    if is_greeting_only(text):
        return "reject"

    if has_workflow_signal(text):
        return "allow"

    return "unknown"