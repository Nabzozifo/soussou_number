# import pandas as pd
# import streamlit as st
# import re
# from rdflib import Graph, URIRef, Literal, Namespace, RDF
# from rdflib.namespace import XSD
# from owlrl import DeductiveClosure, OWLRL_Semantics

# # Load Excel file
# try:
#     df = pd.read_excel("French_Sosso.xlsx", sheet_name='Number')
# except Exception as e:
#     st.error(f"Error loading Excel file: {str(e)}")
#     st.stop()

# # Namespaces
# EX = Namespace("http://example.org/numkg/")
# MATH = Namespace("http://example.org/math/")
# g = Graph()
# g.bind("ex", EX)
# g.bind("math", MATH)

# # Clean helper


# def clean(val):
#     if pd.isna(val):
#         return "unknown"
#     return str(val).strip().lower().replace(" ", "_").replace(",", "").replace("–", "-")


# # Add triples to the graph
# for _, row in df.iterrows():
#     try:
#         soussou = clean(row['Soussou'])
#         french = Literal(str(row['French']).strip(), datatype=XSD.string)
#         form = Literal(str(row['Commentaire']).strip(), datatype=XSD.string) if pd.notna(
#             row['Commentaire']) else Literal("unknown", datatype=XSD.string)

#         s_uri = URIRef(EX[soussou])
#         g.add((s_uri, EX.translation_french, french))
#         g.add((s_uri, EX.has_form, form))

#         if 'Valeur' in df.columns and pd.notna(row['Valeur']):
#             try:
#                 value = int(float(row['Valeur']))
#                 g.add((s_uri, EX.value, Literal(value, datatype=XSD.integer)))
#             except (ValueError, TypeError):
#                 pass

#         if pd.notna(row['Commentaire']) and "décomposée" in str(row['Commentaire']).lower():
#             parts = soussou.split("_nun_")
#             for part in parts:
#                 part_uri = URIRef(EX[clean(part)])
#                 g.add((s_uri, EX.composedOf, part_uri))
#     except Exception as e:
#         st.warning(f"Error processing row {_}: {str(e)}")
#         continue

# # Add mathematical composition rules


# def add_composition_rules():
#     # Define mathematical operations
#     g.add((MATH.addition, RDF.type, MATH.Operation))
#     g.add((MATH.addition, EX.symbol, Literal("+")))

#     # Rule: If x is composed of a and b, then x = a + b
#     # This is handled in the inference function rather than as RDF rules


# add_composition_rules()

# # Apply OWL-RL reasoning
# try:
#     DeductiveClosure(OWLRL_Semantics).expand(g)
# except Exception as e:
#     st.warning(f"Reasoning error: {str(e)}")

# # Function to get direct Soussou translation


# def get_direct_translation(number):
#     query = """
#         PREFIX ex: <http://example.org/numkg/>
#         SELECT ?soussou
#         WHERE {
#             ?soussou ex:value ?val .
#             FILTER(?val = """ + str(number) + """)
#         }
#     """
#     qres = g.query(query)
#     return [str(row.soussou).split("/")[-1] for row in qres]

# # Function to infer composition of numbers


# def infer_composition(number):
#     if number <= 20:  # Typically these are atomic terms
#         return []

#     # Try to decompose the number (this should match your language's number composition rules)
#     components = []
#     remaining = number

#     # Check for tens (assuming base-20 like many African numbering systems)
#     if remaining >= 20:
#         tens = (remaining // 20) * 20
#         components.append(tens)
#         remaining -= tens

#     # Check for intermediate terms (10, 15, etc. if they exist in your system)
#     if remaining >= 10:
#         components.append(10)
#         remaining -= 10

#     # Add remaining units
#     if remaining > 0:
#         components.append(remaining)

#     # Verify all components exist in our KB
#     valid_components = []
#     for comp in components:
#         if get_direct_translation(comp):
#             valid_components.append(comp)
#         else:
#             # If a component doesn't exist, try to decompose it further
#             sub_components = infer_composition(comp)
#             if sub_components:
#                 valid_components.extend(sub_components)
#             else:
#                 return []  # Can't decompose

#     return valid_components

# # Function to build composite name


# def build_composite_name(components):
#     names = []
#     for num in components:
#         trans = get_direct_translation(num)
#         if trans:
#             names.append(trans[0])
#         else:
#             return None
#     return "_nun_".join(names)

# # Main translation function


# def get_soussou_translation(number):
#     # First try direct translation
#     direct = get_direct_translation(number)
#     if direct:
#         return direct, "direct"

#     # Try to infer composition
#     components = infer_composition(number)
#     if components:
#         composite_name = build_composite_name(components)
#         if composite_name:
#             # Add inferred knowledge to the graph (in memory only)
#             s_uri = URIRef(EX[composite_name])
#             g.add((s_uri, EX.value, Literal(number, datatype=XSD.integer)))
#             g.add((s_uri, EX.has_form, Literal(
#                 "inferred_composition", datatype=XSD.string)))
#             for comp in components:
#                 comp_uri = URIRef(EX[get_direct_translation(comp)[0]])
#                 g.add((s_uri, EX.composedOf, comp_uri))
#             return [composite_name], "inferred"

#     return [], "not_found"


# # Streamlit UI
# st.title("Soussou Number Translator with Inference")
# st.write("This app translates French numbers into Soussou, with inference for composite numbers.")

# question = st.text_input(
#     "Posez une question (e.g., C'est quoi 32 en Soussou ?):", "C'est quoi 32 en Soussou ?")

# # Normalize the question
# normalized_question = question.strip().lower()
# translation_pattern = r"(?:c'est quoi|quel est|tradui[st]|comment dit-on)\s*(\d+)\s*(?:en|en langue)?\s*soussou"
# match = re.search(translation_pattern, normalized_question, re.IGNORECASE)

# if match:
#     try:
#         number = int(match.group(1))
#         translations, source = get_soussou_translation(number)

#         if translations:
#             if source == "direct":
#                 st.success(
#                     f"Le mot en Soussou pour {number} est: {', '.join(translations)}")
#             else:
#                 st.success(
#                     f"Le mot en Soussou pour {number} (inféré par composition) est: {', '.join(translations)}")
#                 st.info(
#                     f"Composition: {' + '.join(str(c) for c in infer_composition(number))}")
#         else:
#             st.warning(
#                 f"Nous n'avons pas pu trouver ou déduire le mot Soussou pour {number}.")
#     except Exception as e:
#         st.error(f"Erreur de traitement: {str(e)}")
# else:
#     st.info("""
#         Posez une question comme:
#         - C'est quoi 5 en Soussou ?
#         - Quel est 32 en langue Soussou ?
#         - Traduis 15 en Soussou
#     """)

import pandas as pd
import streamlit as st
import re
import random
from rdflib import Graph, URIRef, Literal, Namespace, RDF
from rdflib.namespace import XSD
from owlrl import DeductiveClosure, OWLRL_Semantics
from gtts import gTTS
import os
import math

# Load Excel file
try:
    df = pd.read_excel("French_Sosso.xlsx", sheet_name='Number')
except Exception as e:
    st.error(f"Error loading Excel file: {str(e)}")
    st.stop()

# Namespaces
EX = Namespace("http://example.org/numkg/")
MATH = Namespace("http://example.org/math/")
g = Graph()
g.bind("ex", EX)
g.bind("math", MATH)

# Clean helper


def clean(val):
    if pd.isna(val):
        return "unknown"
    return str(val).strip().lower().replace(" ", "_").replace(",", "").replace("–", "-")


# Add triples to the graph
for _, row in df.iterrows():
    try:
        soussou = clean(row['Soussou'])
        french = Literal(str(row['French']).strip(), datatype=XSD.string)
        form = Literal(str(row['Commentaire']).strip(), datatype=XSD.string) if pd.notna(
            row['Commentaire']) else Literal("unknown", datatype=XSD.string)

        s_uri = URIRef(EX[soussou])
        g.add((s_uri, EX.translation_french, french))
        g.add((s_uri, EX.has_form, form))

        if 'Valeur' in df.columns and pd.notna(row['Valeur']):
            try:
                value = int(float(row['Valeur']))
                g.add((s_uri, EX.value, Literal(value, datatype=XSD.integer)))
            except (ValueError, TypeError):
                pass

        if pd.notna(row['Commentaire']) and "décomposée" in str(row['Commentaire']).lower():
            parts = soussou.split("_nun_")
            for part in parts:
                part_uri = URIRef(EX[clean(part)])
                g.add((s_uri, EX.composedOf, part_uri))
    except Exception as e:
        st.warning(f"Error processing row {_}: {str(e)}")
        continue

# Add mathematical operations to the knowledge graph


def add_math_operations():
    operations = {
        "addition": "+",
        "soustraction": "-",
        "multiplication": "×",
        "division": "÷",
        "puissance": "^",
        "racine": "√"
    }

    for op, symbol in operations.items():
        op_uri = URIRef(MATH[op])
        g.add((op_uri, RDF.type, MATH.Operation))
        g.add((op_uri, MATH.symbol, Literal(symbol)))


add_math_operations()

# Apply OWL-RL reasoning
try:
    DeductiveClosure(OWLRL_Semantics).expand(g)
except Exception as e:
    st.warning(f"Reasoning error: {str(e)}")

# Translation functions


def get_direct_translation(number):
    query = """
        PREFIX ex: <http://example.org/numkg/>
        SELECT ?soussou
        WHERE {
            ?soussou ex:value ?val .
            FILTER(?val = """ + str(number) + """)
        }
    """
    qres = g.query(query)
    return [str(row.soussou).split("/")[-1] for row in qres]


def infer_composition(number):
    if number <= 20:
        return []

    components = []
    remaining = number

    # Handle base-20 system
    if remaining >= 20:
        tens = (remaining // 20) * 20
        components.append(tens)
        remaining -= tens

    if remaining >= 10:
        components.append(10)
        remaining -= 10

    if remaining > 0:
        components.append(remaining)

    valid_components = []
    for comp in components:
        if get_direct_translation(comp):
            valid_components.append(comp)
        else:
            sub_components = infer_composition(comp)
            if sub_components:
                valid_components.extend(sub_components)
            else:
                return []

    return valid_components


def build_composite_name(components):
    names = []
    for num in components:
        trans = get_direct_translation(num)
        if trans:
            names.append(trans[0])
        else:
            return None
    return "_nun_".join(names)


def get_soussou_translation(number):
    direct = get_direct_translation(number)
    if direct:
        return direct, "direct"

    components = infer_composition(number)
    if components:
        composite_name = build_composite_name(components)
        if composite_name:
            s_uri = URIRef(EX[composite_name])
            g.add((s_uri, EX.value, Literal(number, datatype=XSD.integer)))
            g.add((s_uri, EX.has_form, Literal(
                "inferred_composition", datatype=XSD.string)))
            for comp in components:
                comp_uri = URIRef(EX[get_direct_translation(comp)[0]])
                g.add((s_uri, EX.composedOf, comp_uri))
            return [composite_name], "inferred"

    return [], "not_found"

# Advanced Math Operations


def perform_math_operation(operation, num1, num2=None):
    try:
        if operation == "addition":
            result = num1 + num2
        elif operation == "soustraction":
            result = num1 - num2
        elif operation == "multiplication":
            result = num1 * num2
        elif operation == "division":
            result = num1 / num2 if num2 != 0 else None
        elif operation == "puissance":
            result = num1 ** num2
        elif operation == "racine":
            result = math.sqrt(num1)
        else:
            return None

        return result if result is not None else "Undefined"
    except:
        return "Error"


def translate_math_question(question):
    operation_map = {
        "somme": "addition",
        "addition": "addition",
        "plus": "addition",
        "produit": "multiplication",
        "multiplication": "multiplication",
        "fois": "multiplication",
        "différence": "soustraction",
        "soustraction": "soustraction",
        "moins": "soustraction",
        "quotient": "division",
        "division": "division",
        "divisé": "division",
        "puissance": "puissance",
        "exposant": "puissance",
        "racine": "racine"
    }

    question = question.lower().strip()

    # Handle square root first
    if "racine" in question:
        match = re.search(r"racine.*?(\d+)", question)
        if match:
            num = int(match.group(1))
            return "racine", num, None  # operation, num1, num2
        return None, None, None

    # Handle other operations
    for fr_term, operation in operation_map.items():
        if fr_term in question:
            # Match patterns like: "somme de 5 et 3" or "produit de 10 par 2"
            match = re.search(rf"{fr_term}.*?(\d+).*?(\d+)", question)
            if match:
                num1 = int(match.group(1))
                num2 = int(match.group(2))
                return operation, num1, num2

    # If no operation found, try to extract simple expression like "3 + 5"
    match = re.search(r"(\d+)\s*([+\-*/^])\s*(\d+)", question)
    if match:
        num1 = int(match.group(1))
        operator = match.group(2)
        num2 = int(match.group(3))

        operator_map = {
            '+': 'addition',
            '-': 'soustraction',
            '*': 'multiplication',
            '/': 'division',
            '^': 'puissance'
        }

        if operator in operator_map:
            return operator_map[operator], num1, num2

    return None, None, None


# Interactive Number Formation


def show_number_formation(number):
    components = infer_composition(number)
    if not components:
        return None

    chart_data = []
    for comp in components:
        trans = get_direct_translation(comp)
        french = next((str(row['French']) for _, row in df.iterrows()
                      if pd.notna(row.get('Valeur')) and int(row['Valeur']) == comp), "?")
        chart_data.append({
            "Valeur": comp,
            "Soussou": trans[0] if trans else "?",
            "Français": french,
            "Composant": f"{comp} = {french}"
        })

    return chart_data, " + ".join(str(c) for c in components)

# Text-to-Speech


def generate_pronunciation(text, language='fr'):
    try:
        tts = gTTS(text=text.replace("_", " "), lang=language, slow=True)
        filename = f"temp_{hash(text)}.mp3"
        tts.save(filename)
        return filename
    except:
        return None


# Streamlit UI
st.title("🔢 Système Numérique Soussou avec Opérations Avancées")
st.markdown("""
    *Traducteur de nombres avec raisonnement mathématique et guide interactif*
""")

tab1, tab2, tab3 = st.tabs(
    ["Traduction", "Opérations Mathématiques", "Formation des Nombres"])

with tab1:
    st.header("Traduction de Nombres")
    question = st.text_input("Posez une question (ex: 'C'est quoi 25 en Soussou ?'):",
                             "C'est quoi 25 en Soussou ?")

    normalized_question = question.strip().lower()
    match = re.search(r"(?:c'est quoi|quel est|tradui[st]|comment dit-on)\s*(\d+)\s*(?:en|en langue)?\s*soussou",
                      normalized_question, re.IGNORECASE)

    if match:
        number = int(match.group(1))
        translations, source = get_soussou_translation(number)

        if translations:
            st.success(
                f"**{number} en Soussou:** {translations[0].replace('_', ' ')}")

            # Pronunciation
            audio_file = generate_pronunciation(translations[0])
            if audio_file:
                st.audio(audio_file, format='audio/mp3')
                os.remove(audio_file)

            if source == "inferred":
                components = infer_composition(number)
                st.info(
                    f"**Composition:** {' + '.join(str(c) for c in components)}")
        else:
            st.warning(
                f"Nous n'avons pas pu trouver ou déduire le mot Soussou pour {number}.")

with tab2:
    st.header("Opérations Mathématiques")
    math_question = st.text_input("Posez une question mathématique (ex: 'Quel est le produit de 3 et 5 ?'):",
                                  "Quel est le produit de 3 et 5 ?")

    op, num1, num2 = translate_math_question(math_question)

    if op:
        result = perform_math_operation(op, num1, num2)

        if isinstance(result, (int, float)):
            # Display the operation and result
            operator_symbol = {
                'addition': '+',
                'soustraction': '-',
                'multiplication': '×',
                'division': '÷',
                'puissance': '^',
                'racine': '√'
            }.get(op, op)

            if op == 'racine':
                operation_str = f"√{num1} = {result}"
            else:
                operation_str = f"{num1} {operator_symbol} {num2} = {result}"

            st.write(f"**Opération:** {operation_str}")

            # Get Soussou translation
            trans, _ = get_soussou_translation(int(result))
            if trans:
                st.success(
                    f"**Résultat en Soussou:** {trans[0].replace('_', ' ')}")
            else:
                st.warning("Nous ne pouvons pas traduire ce résultat.")
        else:
            st.error(f"Erreur de calcul: {result}")
    else:
        st.info("""
            Formulez votre question comme:
            - "Quel est le produit de 3 et 5 ?"
            - "Quelle est la somme de 10 et 15 ?"
            - "Calculer la racine carrée de 16"
            - "3 + 5 en Soussou"
        """)

with tab3:
    st.header("Guide Interactif de Formation des Nombres")
    number_to_analyze = st.number_input(
        "Entrez un nombre à analyser:", min_value=1, max_value=1000, value=32)

    formation_data, formula = show_number_formation(number_to_analyze)

    if formation_data:
        st.write("**Décomposition:**")
        col1, col2 = st.columns(2)

        with col1:
            st.table(pd.DataFrame(formation_data))

        with col2:
            st.latex(f"{formula} = {number_to_analyze}")

        # Visual tree
        tree = {"name": str(number_to_analyze), "children": []}
        for comp in formation_data:
            tree["children"].append({
                "name": f"{comp['Valeur']} ({comp['Soussou']})",
                "children": []
            })

        st.write("**Représentation arborescente:**")
        st.json(tree, expanded=False)
    else:
        st.warning(
            "Nous ne pouvons pas décomposer ce nombre avec les données actuelles.")

# Add cultural notes
cultural_notes = {
    20: "20 est une base importante dans le système numérique Soussou",
    40: "40 est considéré comme un nombre significatif dans la culture",
    100: "100 représente une grande quantité dans les expressions traditionnelles"
}

note = cultural_notes.get(
    number_to_analyze if 'number_to_analyze' in locals() else 0)
if note:
    st.info(f"**Note culturelle:** {note}")
